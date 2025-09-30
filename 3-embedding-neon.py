import argparse
from typing import List
import json
import os
import glob
import sys
import warnings
import psycopg2
from psycopg2.extras import Json
import numpy as np

from docling.chunking import HierarchicalChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from openai import OpenAI
from mistralai import Mistral

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate embeddings for document chunks and store in Neon database')
parser.add_argument('--embedding-provider', type=str, default=None,
                    help='Embedding provider: openai or mistral')
parser.add_argument('--openai-api-key', type=str, default=None,
                    help='OpenAI API key (required if using OpenAI)')
parser.add_argument('--mistral-api-key', type=str, default=None,
                    help='Mistral API key (required if using Mistral)')
args = parser.parse_args()

# Load environment variables as fallback
load_dotenv()

# Neon database connection - loaded from environment variables
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

# Validate required environment variables
if not NEON_CONNECTION_STRING:
    print("NEON_CONNECTION_STRING environment variable is required but not set!")
    exit(1)

# Set up Unicode encoding for Windows console and suppress warnings
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning)

# Determine embedding provider - command line args take precedence
if args.embedding_provider:
    embedding_provider = args.embedding_provider.lower()
else:
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

# Initialize clients based on provider
openai_client = None
mistral_client = None

if embedding_provider == "openai":
    # Get API key - command line args take precedence over env vars
    api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key is required. Provide it via --openai-api-key argument or OPENAI_API_KEY environment variable.")
        exit(1)
    openai_client = OpenAI(api_key=api_key)
    print("Using OpenAI for embeddings")
elif embedding_provider == "mistral":
    # Get API key - command line args take precedence over env vars
    api_key = args.mistral_api_key or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("Mistral API key is required. Provide it via --mistral-api-key argument or MISTRAL_API_KEY environment variable.")
        exit(1)
    mistral_client = Mistral(api_key=api_key)
    print("Using Mistral for embeddings")
else:
    print("Invalid EMBEDDING_PROVIDER. Use 'openai' or 'mistral'")
    exit(1)

MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

# Initialize DocumentConverter
converter = DocumentConverter()

# Neon database connection - loaded from environment variables
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

def get_db_connection():
    """Get connection to Neon database"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        # Test the connection
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"Connection string: {NEON_CONNECTION_STRING[:50]}...")
        return None

def initialize_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database for initialization")
        return False

    try:
        with conn.cursor() as cur:
            # Create documents table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size BIGINT,
                    file_type TEXT,
                    content TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_date TIMESTAMP
                )
            """)

            # Create document_chunks table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    page_numbers TEXT,
                    section_title TEXT,
                    chunk_type TEXT DEFAULT 'text',
                    token_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create embeddings table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id SERIAL PRIMARY KEY,
                    chunk_id INTEGER REFERENCES document_chunks(id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    original_filename TEXT,
                    page_numbers TEXT,
                    title TEXT,
                    embedding_vector vector(1536),
                    embedding_provider TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create processing_logs table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    process_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("✅ Database tables initialized successfully")
            return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def clear_existing_embeddings(provider):
    """Clear existing embeddings for the provider"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM embeddings WHERE embedding_provider = %s", (provider,))
                conn.commit()
                print(f"Cleared existing embeddings for {provider}")
        except Exception as e:
            print(f"Error clearing embeddings: {e}")
        finally:
            conn.close()

def store_embedding_in_db(chunk_data, embedding_vector, provider, model):
    """Store embedding in Neon database"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database for embedding insertion")
        return False

    try:
        with conn.cursor() as cur:
            # First verify the chunk exists
            cur.execute("SELECT id, document_id FROM document_chunks WHERE id = %s", (chunk_data["chunk_id"],))
            chunk_result = cur.fetchone()
            if not chunk_result:
                print(f"❌ Chunk with ID {chunk_data['chunk_id']} not found")
                return False

            chunk_id, document_id = chunk_result
            print(f"💾 Storing embedding for chunk {chunk_id} from document: {chunk_data['filename']}")

            # Convert embedding vector to PostgreSQL vector format
            embedding_array = np.array(embedding_vector).astype('float32')

            # Store embedding with chunk reference
            cur.execute("""
                INSERT INTO embeddings
                (chunk_id, filename, original_filename, page_numbers, title, text, embedding_vector, embedding_provider, embedding_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                chunk_data["chunk_id"],
                chunk_data["filename"],
                chunk_data["original_filename"],
                Json(chunk_data["page_numbers"]) if chunk_data["page_numbers"] else None,
                chunk_data["section_title"],  # Use section_title as title
                chunk_data.get("text", chunk_data.get("chunk_text", "")),  # Include chunk text
                embedding_array.tolist(),
                provider,
                model
            ))

            embedding_id = cur.fetchone()[0]
            conn.commit()
            print(f"✅ Embedding stored successfully (ID: {embedding_id})")
            return True
    except Exception as e:
        print(f"❌ Error storing embedding for chunk {chunk_data['chunk_id']}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# --------------------------------------------------------------
# Read from Neon database documents table
# --------------------------------------------------------------

def get_chunks_from_db():
    """Get document chunks from Neon database that need embedding processing"""
    conn = get_db_connection()
    if not conn:
        raise Exception("Could not connect to Neon database")

    try:
        with conn.cursor() as cur:
            # First, let's check what chunks exist in total
            cur.execute("SELECT COUNT(*) FROM document_chunks")
            total_chunks = cur.fetchone()[0]
            print(f"📊 Total chunks in database: {total_chunks}")

            # Check what embeddings exist for this provider
            cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_provider = %s", (embedding_provider,))
            existing_embeddings = cur.fetchone()[0]
            print(f"📊 Existing embeddings for {embedding_provider}: {existing_embeddings}")

            # Check if chunks already have embeddings from other providers
            cur.execute("""
                SELECT dc.id, e.embedding_provider, e.embedding_model
                FROM document_chunks dc
                JOIN embeddings e ON dc.id = e.chunk_id
            """)
            existing_embeddings = cur.fetchall()
            print(f"📊 Total existing embeddings: {len(existing_embeddings)}")
            for emb in existing_embeddings[:3]:  # Show first 3
                chunk_id, provider, model = emb
                print(f"  • Chunk {chunk_id}: {provider} ({model})")
            if len(existing_embeddings) > 3:
                print(f"  • ... and {len(existing_embeddings) - 3} more")

            # Get chunks that don't have embeddings yet for this provider
            print(f"🔍 Looking for chunks that need {embedding_provider} embeddings...")
            cur.execute("""
                SELECT dc.id, dc.document_id, dc.chunk_text, dc.chunk_index,
                       dc.page_numbers, dc.section_title, dc.chunk_type, dc.token_count,
                       d.filename as document_filename
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                LEFT JOIN embeddings e ON dc.id = e.chunk_id AND e.embedding_provider = %s
                WHERE e.id IS NULL
            """, (embedding_provider,))

            chunks = cur.fetchall()
            print(f"🔍 Found {len(chunks)} chunks that need embedding for {embedding_provider}")

            # If no chunks need embedding, try a different approach
            if len(chunks) == 0:
                print("⚠️ No chunks found with current filter, trying alternative approach...")

                # Try getting chunks without provider filter
                cur.execute("""
                    SELECT dc.id, dc.document_id, dc.chunk_text, dc.chunk_index,
                           dc.page_numbers, dc.section_title, dc.chunk_type, dc.token_count,
                           d.filename as document_filename
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                """)

                all_chunks = cur.fetchall()
                print(f"📊 Total chunks in database: {len(all_chunks)}")

                if len(all_chunks) > 0:
                    print("✅ Found chunks! The issue might be with provider filtering.")
                    print("💡 Trying to process chunks that don't have current provider embeddings...")

                    # Filter out chunks that already have embeddings from current provider
                    chunks_needing_current_provider = []
                    for chunk in all_chunks:
                        chunk_id = chunk[0]
                        cur.execute("""
                            SELECT COUNT(*) FROM embeddings
                            WHERE chunk_id = %s AND embedding_provider = %s
                        """, (chunk_id, embedding_provider))

                        existing_count = cur.fetchone()[0]
                        if existing_count == 0:
                            chunks_needing_current_provider.append(chunk)

                    print(f"🔍 Found {len(chunks_needing_current_provider)} chunks that need {embedding_provider} embeddings")
                    chunks = chunks_needing_current_provider
                else:
                    print("❌ No chunks found in database at all")

            # Show details of chunks found
            for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
                chunk_id, document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count, document_filename = chunk
                print(f"  {i}. Chunk {chunk_index} from {document_filename} ({len(chunk_text)} chars)")

            if len(chunks) > 3:
                print(f"  ... and {len(chunks) - 3} more chunks")

            return chunks
    except Exception as e:
        print(f"❌ Error querying chunks: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

# Initialize database
print("🔧 Initializing database...")
if not initialize_database():
    print("❌ Failed to initialize database")
    exit(1)

# Get chunks from database
chunks = get_chunks_from_db()

if not chunks:
    print("❌ No document chunks found in database that need embedding processing.")
    print("Please ensure documents are uploaded, processed, and chunked first.")

    # Show database status for debugging
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM documents")
                total_docs = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM document_chunks")
                total_chunks = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM embeddings")
                total_embeddings = cur.fetchone()[0]
                print(f"📊 Database status: {total_docs} documents, {total_chunks} chunks, {total_embeddings} embeddings")

                # Show recent documents and chunks for debugging
                print("\n🔍 Recent documents:")
                cur.execute("SELECT id, filename, processed FROM documents ORDER BY upload_date DESC LIMIT 3")
                docs = cur.fetchall()
                for doc in docs:
                    print(f"  • Doc {doc[0]}: {doc[1]} ({'processed' if doc[2] else 'unprocessed'})")

                print("\n🔍 Recent chunks:")
                cur.execute("""
                    SELECT dc.id, d.filename, dc.chunk_index, LENGTH(dc.chunk_text) as text_length
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    ORDER BY dc.created_at DESC LIMIT 3
                """)
                chunks_debug = cur.fetchall()
                for chunk in chunks_debug:
                    print(f"  • Chunk {chunk[0]}: {chunk[1]} (index {chunk[2]}, {chunk[3]} chars)")

        except Exception as e:
            print(f"❌ Error querying database for debug info: {e}")
        finally:
            conn.close()

    print("\n💡 If you have documents and chunks, but this script can't find them,")
    print("   the issue might be with the embedding provider filter.")
    print(f"   Current provider: {embedding_provider}")

    exit(1)

print(f"🔍 Found {len(chunks)} chunk(s) in database that need embedding processing")

# Clear existing embeddings for this provider
clear_existing_embeddings(embedding_provider)

print(f"🚀 Total chunks to process: {len(chunks)}")

# --------------------------------------------------------------
# Generate embeddings using configured provider and store in Neon
# --------------------------------------------------------------

def get_embedding(text):
    """Get embedding for text using configured provider"""
    if embedding_provider == "openai":
        response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    elif embedding_provider == "mistral":
        response = mistral_client.embeddings.create(
            model="mistral-embed",
            inputs=[text]
        )
        return response.data[0].embedding

# Process chunks and generate embeddings
successful_stores = 0
failed_stores = 0

print(f"🧬 Starting embedding generation using {embedding_provider}...")
print(f"📝 Processing {len(chunks)} chunks...")

# Test embedding insertion with actual chunk from database
print("🧪 Testing embedding insertion with real chunk...")
if chunks:
    # Use the first real chunk for testing
    first_chunk = chunks[0]
    chunk_id, document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count, document_filename = first_chunk

    test_chunk_info = {
        "chunk_id": chunk_id,
        "chunk_text": chunk_text[:100] + "...",  # Use partial text for test
        "text": chunk_text[:100] + "...",  # Also include as text for consistency
        "filename": document_filename,
        "original_filename": document_filename,
        "page_numbers": page_numbers,
        "section_title": section_title,
        "chunk_type": chunk_type,
        "token_count": token_count
    }

    test_embedding = [0.1] * 1536  # Test embedding vector
    print(f"🧪 Testing insertion for real chunk {chunk_id} from {document_filename}...")

    if store_embedding_in_db(test_chunk_info, test_embedding, embedding_provider, "test-model"):
        print("✅ Test embedding insertion successful!")

        # Verify it was stored
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM embeddings
                        WHERE chunk_id = %s AND embedding_provider = %s
                    """, (chunk_id, embedding_provider))
                    test_count = cur.fetchone()[0]
                    if test_count > 0:
                        print(f"✅ Verified: Test embedding stored in database for chunk {chunk_id}")

                        # Clean up test embedding
                        cur.execute("DELETE FROM embeddings WHERE chunk_id = %s AND embedding_provider = %s", (chunk_id, embedding_provider))
                        conn.commit()
                        print("🗑️ Cleaned up test embedding")
                    else:
                        print(f"⚠️ Test embedding not found in database verification for chunk {chunk_id}")
            except Exception as e:
                print(f"❌ Error verifying test embedding: {e}")
            finally:
                conn.close()
    else:
        print("❌ Test embedding insertion failed!")
else:
    print("⚠️ No chunks available for testing")

for i, chunk_data in enumerate(chunks):
    try:
        chunk_id, document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count, document_filename = chunk_data

        print(f"🔄 Processing chunk {i+1}/{len(chunks)} from {document_filename} (Chunk ID: {chunk_id})...")

        # Get embedding from provider
        print(f"🤖 Generating embedding using {embedding_provider}...")
        embedding = get_embedding(chunk_text)
        print(f"✅ Generated embedding vector with {len(embedding)} dimensions")

        # Prepare chunk data for storage
        chunk_info = {
            "chunk_id": chunk_id,
            "text": chunk_text,
            "filename": document_filename,
            "original_filename": document_filename,
            "page_numbers": page_numbers,
            "section_title": section_title,
            "chunk_type": chunk_type,
            "token_count": token_count
        }

        # Store in database
        model = "text-embedding-3-large" if embedding_provider == "openai" else "mistral-embed"
        print(f"💾 Storing embedding in database for chunk {chunk_id}...")
        if store_embedding_in_db(chunk_info, embedding, embedding_provider, model):
            successful_stores += 1
            print(f"✅ Successfully stored embedding {i+1}/{len(chunks)} for {document_filename}")

            # Verify the embedding was actually stored
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT COUNT(*) FROM embeddings
                            WHERE chunk_id = %s AND embedding_provider = %s
                        """, (chunk_id, embedding_provider))
                        stored_count = cur.fetchone()[0]
                        if stored_count > 0:
                            print(f"✅ Verified: Embedding stored in database for chunk {chunk_id}")
                        else:
                            print(f"⚠️ Warning: Embedding not found in database verification for chunk {chunk_id}")
                except Exception as e:
                    print(f"❌ Error verifying embedding storage: {e}")
                finally:
                    conn.close()
        else:
            failed_stores += 1
            print(f"❌ Failed to store embedding {i+1}/{len(chunks)} for {document_filename}")

    except Exception as e:
        failed_stores += 1
        print(f"❌ Error processing chunk {i+1}: {e}")
        import traceback
        traceback.print_exc()
        continue

# Final verification
print("\n🎉 Embedding generation completed!")
print(f"📊 Results: {successful_stores} successful, {failed_stores} failed")

# Verify embeddings were actually stored
conn = get_db_connection()
if conn:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_provider = %s", (embedding_provider,))
            total_embeddings = cur.fetchone()[0]
            print(f"📊 Total embeddings in database for {embedding_provider}: {total_embeddings}")
    except Exception as e:
        print(f"❌ Error verifying embeddings: {e}")
    finally:
        conn.close()

if successful_stores > 0:
    print("✅ Embeddings successfully stored in Neon database!")
    print(f"🚀 You can now use the chat interface to ask questions about your document: {document_filename}")
else:
    print("❌ No embeddings were successfully stored")
    print("💡 Check the error messages above for troubleshooting information")