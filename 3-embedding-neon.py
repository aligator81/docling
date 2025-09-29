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
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

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
    if conn:
        try:
            with conn.cursor() as cur:
                # Convert embedding vector to PostgreSQL vector format
                embedding_array = np.array(embedding_vector).astype('float32')
                
                # Store embedding with chunk reference - match actual schema
                cur.execute("""
                    INSERT INTO embeddings
                    (chunk_id, text, filename, original_filename, page_numbers, title, embedding_vector, embedding_provider, embedding_model)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk_data["chunk_id"],
                    chunk_data["text"],
                    chunk_data["filename"],
                    chunk_data["original_filename"],
                    Json(chunk_data["page_numbers"]) if chunk_data["page_numbers"] else None,
                    chunk_data["section_title"],  # Use section_title as title
                    embedding_array.tolist(),
                    provider,
                    model
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing embedding: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

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
            # Get chunks that don't have embeddings yet for this provider
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
            return chunks
    finally:
        conn.close()

# Get chunks from database
chunks = get_chunks_from_db()

if not chunks:
    print("No document chunks found in database that need embedding processing.")
    print("Please ensure documents are uploaded, processed, and chunked first.")
    exit(0)

print(f"Found {len(chunks)} chunk(s) in database that need embedding processing")

# Clear existing embeddings for this provider
clear_existing_embeddings(embedding_provider)

print(f"Total chunks to process: {len(chunks)}")

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
for i, chunk_data in enumerate(chunks):
    try:
        chunk_id, document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count, document_filename = chunk_data
        
        embedding = get_embedding(chunk_text)
        
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
        if store_embedding_in_db(chunk_info, embedding, embedding_provider, model):
            successful_stores += 1
            print(f"✅ Stored chunk {i+1}/{len(chunks)} using {embedding_provider}")
        else:
            print(f"❌ Failed to store chunk {i+1}/{len(chunks)}")
            
    except Exception as e:
        print(f"Error processing chunk: {e}")
        continue

print(f"Successfully stored {successful_stores}/{len(chunks)} chunks in Neon database using {embedding_provider}")
print("You can now use 4-search-neon.py to search through these embeddings in the Neon database")