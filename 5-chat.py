import streamlit as st
import json
import numpy as np
import subprocess
import os
import re
import sys
import time
from datetime import datetime
from openai import OpenAI
from mistralai import Mistral
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
import requests
import tempfile
import psycopg2
from psycopg2.extras import Json

# Load environment variables
load_dotenv()

# Neon database connection - loaded from environment variables
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

# Validate required environment variables
if not NEON_CONNECTION_STRING:
    st.error("❌ NEON_CONNECTION_STRING environment variable is required but not set!")
    st.error("Please set NEON_CONNECTION_STRING in your Coolify environment variables.")
    st.error("Example: postgresql://username:password@host/database")
    st.error(f"Current value: {os.getenv('NEON_CONNECTION_STRING', 'NOT SET')}")
    st.stop()

# Initialize session state for API keys and settings
if "api_keys_configured" not in st.session_state:
    st.session_state.api_keys_configured = False
if "openai_client" not in st.session_state:
    st.session_state.openai_client = None
if "mistral_client" not in st.session_state:
    st.session_state.mistral_client = None
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "openai"
if "embedding_provider" not in st.session_state:
    st.session_state.embedding_provider = "openai"
if "extraction_provider" not in st.session_state:
    st.session_state.extraction_provider = "docling"
# Initialize session state for uploaded documents
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []
    
    # Auto-reload uploaded documents from disk
    uploads_dir = "data/uploads"
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, filename)
            if os.path.isfile(filepath):
                try:
                    file_size = os.path.getsize(filepath)
                    upload_time = datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%H:%M:%S")
                    doc_info = {
                        "name": filename,
                        "size": f"{file_size / 1024:.1f} KB",
                        "upload_time": upload_time,
                        "source_path": filepath
                    }
                    st.session_state.uploaded_documents.append(doc_info)
                except Exception as e:
                    st.error(f"Error loading file {filename}: {e}")

def configure_api_keys():
    """Display API key configuration interface"""
    st.markdown("### 🔑 API Configuration")
    st.markdown("Please configure your API keys to get started:")
    
    # LLM Provider selection
    provider_choice = st.selectbox(
        "Choose your LLM Provider:",
        options=["openai", "mistral"],
        index=0 if st.session_state.llm_provider == "openai" else 1,
        help="Select which LLM provider you want to use for chat responses"
    )
    
    # API Key inputs
    col1, col2 = st.columns(2)
    
    # Embedding provider selection
    st.markdown("#### Embedding Provider")
    embedding_provider = st.selectbox(
        "Choose Embedding Provider:",
        options=["openai", "mistral"],
        index=0,
        help="Select which provider to use for text embeddings"
    )
    
    # Extraction provider selection
    st.markdown("#### Extraction Provider")
    extraction_provider = st.selectbox(
        "Choose Extraction Provider:",
        options=["docling", "mistral"],
        index=0,
        help="Select which provider to use for document extraction (Docling = local, Mistral = cloud OCR)"
    )
    
    with col1:
        st.markdown("#### OpenAI Configuration")
        openai_key = st.text_input(
            "OpenAI API Key:",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help=f"Required for chat (if using OpenAI) and embeddings (if using OpenAI for embeddings)",
            placeholder="sk-...",
            disabled=(provider_choice == "mistral" and embedding_provider == "mistral")
        )
        openai_model = st.selectbox(
            "OpenAI Chat Model:",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0,
            help="Choose your preferred OpenAI model",
            disabled=(provider_choice == "mistral")
        )
    
    with col2:
        st.markdown("#### Mistral Configuration")
        mistral_key = st.text_input(
            "Mistral API Key:",
            type="password",
            value=os.getenv("MISTRAL_API_KEY", ""),
            help="Required for chat (if using Mistral) and embeddings (if using Mistral for embeddings)",
            placeholder="your-mistral-key",
            disabled=(provider_choice == "openai" and embedding_provider == "openai")
        )
        mistral_model = st.selectbox(
            "Mistral Chat Model:",
            options=["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"],
            index=0,
            help="Choose your preferred Mistral model (small recommended for rate limits)",
            disabled=(provider_choice == "openai")
        )
    
    # Configuration notes
    if provider_choice == "mistral":
        st.info("ℹ️ **Note**: Mistral provides both chat and embedding models. You can use Mistral for everything, or optionally keep OpenAI for embeddings.")
    
    # Test and save configuration
    if st.button("🔧 Test & Save Configuration", type="primary"):
        try:
            success = True
            error_messages = []
            
            # Validate OpenAI configuration if needed
            if provider_choice == "openai" or embedding_provider == "openai":
                if not openai_key:
                    error_messages.append("OpenAI API key is required for selected configuration")
                    success = False
                else:
                    try:
                        test_openai_client = OpenAI(api_key=openai_key)
                        # Store the client for later use
                        st.session_state.openai_client = test_openai_client
                        st.session_state.openai_model = openai_model
                    except Exception as e:
                        error_messages.append(f"OpenAI API key validation failed: {str(e)}")
                        success = False
            
            # Validate Mistral configuration if needed
            if provider_choice == "mistral" or embedding_provider == "mistral":
                if not mistral_key:
                    error_messages.append("Mistral API key is required for selected configuration")
                    success = False
                else:
                    try:
                        test_mistral_client = Mistral(api_key=mistral_key)
                        # Store the client for later use
                        st.session_state.mistral_client = test_mistral_client
                        st.session_state.mistral_model = mistral_model
                    except Exception as e:
                        error_messages.append(f"Mistral API key validation failed: {str(e)}")
                        success = False
            
            if success:
                st.session_state.llm_provider = provider_choice
                st.session_state.embedding_provider = embedding_provider
                st.session_state.extraction_provider = extraction_provider
                st.session_state.api_keys_configured = True
                st.success("✅ Configuration successful! You can now use the application.")
                st.rerun()
            else:
                for msg in error_messages:
                    st.error(f"❌ {msg}")
                    
        except Exception as e:
            st.error(f"❌ Configuration failed: {str(e)}")

if not st.session_state.api_keys_configured:
    st.set_page_config(
        page_title="🔑 API Configuration",
        page_icon="🔑",
        layout="wide"
    )
    
    st.title("🔑 LLM API Configuration")
    st.markdown("Welcome! Please configure your API keys to get started with the Document Q&A Assistant.")
    
    configure_api_keys()
    st.stop()

# Check if API keys are configured
if not st.session_state.api_keys_configured:
    st.warning("⚠️ Please configure your API keys in the sidebar to use the application.")
    st.stop()

# Get the configured clients and settings
openai_client = st.session_state.openai_client
mistral_client = st.session_state.mistral_client
llm_provider = st.session_state.llm_provider
embedding_provider = st.session_state.get("embedding_provider", "openai")
extraction_provider = st.session_state.get("extraction_provider", "docling")

def get_db_connection():
    """Get connection to Neon database"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        # Test the connection
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.error(f"Connection string: {NEON_CONNECTION_STRING[:50]}...")
        st.error("Please check:")
        st.error("• NEON_CONNECTION_STRING is set correctly in your .env file")
        st.error("• Your Neon database is running and accessible")
        st.error("• Your IP is whitelisted in Neon if required")
        return None

def search_embeddings_neon(query, top_k=3):
    """Search through embeddings stored in Neon database"""
    try:
        # Check if API keys are configured
        if not st.session_state.api_keys_configured:
            st.error("❌ API keys not configured. Please configure API keys in the sidebar first.")
            return []

        conn = get_db_connection()
        if not conn:
            st.error("❌ Failed to connect to database")
            return []

        try:
            # Get embedding for query with timeout
            st.write(f"🔄 Generating embedding for query using {embedding_provider}...")
            query_embedding = get_embedding(query)
            query_embedding_array = np.array(query_embedding).astype('float32')
            st.write(f"✅ Generated query embedding ({len(query_embedding)} dimensions)")

            # Use vector similarity search
            st.write(f"🔍 Searching database for similar embeddings...")
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, text, filename, original_filename, page_numbers, title,
                        embedding_vector, embedding_provider, embedding_model,
                        1 - (embedding_vector <=> %s::vector) as similarity
                    FROM embeddings
                    WHERE embedding_provider = %s
                    ORDER BY embedding_vector <=> %s::vector
                    LIMIT %s
                """, (query_embedding_array.tolist(), embedding_provider, query_embedding_array.tolist(), top_k))

                results = []
                rows = cur.fetchall()
                st.write(f"📊 Found {len(rows)} potential matches in database")

                for row in rows:
                    result = {
                        "id": row[0],
                        "text": row[1],
                        "filename": row[2],
                        "original_filename": row[3],
                        "page_numbers": row[4],
                        "title": row[5],
                        "embedding": row[6],
                        "embedding_provider": row[7],
                        "embedding_model": row[8],
                        "similarity": float(row[9])
                    }
                    results.append((result["similarity"], result))

                st.write(f"✅ Search completed, returning {len(results)} results")
                return results

        except Exception as e:
            st.error(f"❌ Error searching embeddings: {e}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
            return []
        finally:
            conn.close()

    except Exception as e:
        st.error(f"❌ Unexpected error in search_embeddings_neon: {e}")
        return []

def check_database_has_embeddings(provider):
    """Check if database has embeddings for the specified provider"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # First check if pgvector extension is available
            try:
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                if not cur.fetchone():
                    st.error("❌ pgvector extension not found in database!")
                    st.error("Please enable the pgvector extension in your Neon database.")
                    st.error("You can do this by running: CREATE EXTENSION vector;")
                    return False
            except Exception as e:
                st.warning(f"⚠️ Could not check for pgvector extension: {e}")

            cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_provider = %s", (provider,))
            count = cur.fetchone()[0]
            return count > 0
    except Exception as e:
        st.error(f"Error checking database: {e}")
        return False
    finally:
        conn.close()

def get_documents_from_db():
    """Get all documents from the database"""
    conn = get_db_connection()
    if not conn:
        st.error("❌ Cannot connect to database to fetch documents")
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, filename, file_path, file_size, file_type, upload_date, processed, processing_date
                FROM documents
                ORDER BY upload_date DESC
            """)
            documents = []
            for row in cur.fetchall():
                doc = {
                    "id": row[0],
                    "filename": row[1],
                    "file_path": row[2],
                    "file_size": row[3],
                    "file_type": row[4],
                    "upload_date": row[5],
                    "processed": row[6],
                    "processing_date": row[7]
                }
                documents.append(doc)

            st.info(f"📊 Found {len(documents)} documents in database")
            return documents
    except Exception as e:
        st.error(f"❌ Error fetching documents: {e}")
        return []
    finally:
        conn.close()

def verify_database_integrity():
    """Verify that all local files exist in database and vice versa"""
    issues = []

    # Check local files vs database
    if os.path.exists("data/uploads"):
        local_files = set()
        for filename in os.listdir("data/uploads"):
            filepath = os.path.join("data/uploads", filename)
            if os.path.isfile(filepath):
                local_files.add(filename)

        # Get database files
        db_files = set(doc["filename"] for doc in get_documents_from_db())

        # Find discrepancies
        in_local_not_db = local_files - db_files
        in_db_not_local = db_files - local_files

        if in_local_not_db:
            issues.append(f"⚠️ {len(in_local_not_db)} files in local folder but not in database: {list(in_local_not_db)[:3]}...")

        if in_db_not_local:
            issues.append(f"⚠️ {len(in_db_not_local)} files in database but not in local folder: {list(in_db_not_local)[:3]}...")

    return issues

def debug_database_content():
    """Debug function to show detailed database content"""
    conn = get_db_connection()
    if not conn:
        return "❌ Cannot connect to database"

    try:
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('documents', 'document_chunks', 'embeddings')
            """)
            existing_tables = [row[0] for row in cur.fetchall()]

            debug_info = "📊 **Database Tables Status:**\n"
            for table in ['documents', 'document_chunks', 'embeddings']:
                if table in existing_tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    debug_info += f"  ✅ {table}: {count} records\n"
                else:
                    debug_info += f"  ❌ {table}: table does not exist\n"

            # Get document details
            if 'documents' in existing_tables:
                cur.execute("SELECT COUNT(*) FROM documents")
                doc_count = cur.fetchone()[0]

                debug_info += f"\n📄 **Documents Details ({doc_count} total):**\n"
                cur.execute("""
                    SELECT id, filename, file_size, file_type, processed, upload_date
                    FROM documents
                    ORDER BY upload_date DESC
                """)
                docs = cur.fetchall()
                for doc in docs:
                    doc_id, filename, file_size, file_type, processed, upload_date = doc
                    status = "✅ Processed" if processed else "⏳ Unprocessed"
                    debug_info += f"  • [{doc_id}] {filename} ({file_size} bytes, {file_type}) - {status}\n"

            # Get chunk details
            if 'document_chunks' in existing_tables:
                cur.execute("SELECT COUNT(*) FROM document_chunks")
                chunk_count = cur.fetchone()[0]

                debug_info += f"\n🔪 **Chunks Details ({chunk_count} total):**\n"
                cur.execute("""
                    SELECT dc.id, d.filename, dc.chunk_index, LENGTH(dc.chunk_text) as text_length, dc.token_count
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    ORDER BY dc.created_at DESC
                    LIMIT 10
                """)
                chunks = cur.fetchall()
                for chunk in chunks:
                    chunk_id, filename, chunk_index, text_length, token_count = chunk
                    debug_info += f"  • [{chunk_id}] {filename} Chunk {chunk_index} ({text_length} chars, {token_count} tokens)\n"

            # Get embedding details
            if 'embeddings' in existing_tables:
                cur.execute("SELECT COUNT(*) FROM embeddings")
                embedding_count = cur.fetchone()[0]

                debug_info += f"\n🧬 **Embeddings Details ({embedding_count} total):**\n"
                cur.execute("""
                    SELECT e.id, d.filename, e.embedding_provider, e.embedding_model, e.created_at
                    FROM embeddings e
                    JOIN document_chunks dc ON e.chunk_id = dc.id
                    JOIN documents d ON dc.document_id = d.id
                    ORDER BY e.created_at DESC
                    LIMIT 10
                """)
                embeddings = cur.fetchall()

                # Group by provider
                provider_counts = {}
                for emb in embeddings:
                    emb_id, filename, provider, model, created_at = emb
                    if provider not in provider_counts:
                        provider_counts[provider] = 0
                    provider_counts[provider] += 1

                debug_info += "📊 **Embeddings by Provider:**\n"
                for provider, count in provider_counts.items():
                    debug_info += f"  • {provider}: {count} embeddings\n"

                debug_info += "\n🧬 **Recent Embeddings:**\n"
                for emb in embeddings[:5]:  # Show first 5
                    emb_id, filename, provider, model, created_at = emb
                    debug_info += f"  • [{emb_id}] {filename} - {provider} ({model})\n"

            return debug_info
    except Exception as e:
        return f"❌ Error debugging database: {e}"
    finally:
        conn.close()

def reset_document_for_reprocessing(document_id):
    """Reset a document's processed status and delete its chunks/embeddings"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # Delete related embeddings first
            cur.execute("DELETE FROM embeddings WHERE chunk_id IN (SELECT id FROM document_chunks WHERE document_id = %s)", (document_id,))
            # Delete related chunks
            cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
            # Reset document processed status
            cur.execute("""
                UPDATE documents
                SET processed = FALSE, processing_date = NULL
                WHERE id = %s
            """, (document_id,))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error resetting document: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def sync_local_files_to_database():
    """Sync local files to database"""
    synced_count = 0
    if os.path.exists("data/uploads"):
        for filename in os.listdir("data/uploads"):
            filepath = os.path.join("data/uploads", filename)
            if os.path.isfile(filepath):
                # Check if file is already in database
                documents = get_documents_from_db()
                if not any(doc["filename"] == filename for doc in documents):
                    # Add file to database
                    file_size = os.path.getsize(filepath)
                    file_type = filename.split('.')[-1].lower()

                    content = None
                    if file_type in ['txt', 'md', 'html']:
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except:
                            content = None

                    if insert_document_to_db(filename, filepath, file_size, file_type, content):
                        synced_count += 1

    return synced_count

def get_chunks_from_db():
    """Get all chunks from the database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dc.id, d.filename, dc.chunk_text, dc.chunk_index, dc.page_numbers,
                       dc.section_title, dc.chunk_type, dc.token_count, dc.created_at
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                ORDER BY d.filename, dc.chunk_index
            """)
            chunks = []
            for row in cur.fetchall():
                chunk = {
                    "id": row[0],
                    "filename": row[1],
                    "chunk_text": row[2],
                    "chunk_index": row[3],
                    "page_numbers": row[4],
                    "section_title": row[5],
                    "chunk_type": row[6],
                    "token_count": row[7],
                    "created_at": row[8]
                }
                chunks.append(chunk)
            return chunks
    except Exception as e:
        st.error(f"Error fetching chunks: {e}")
        return []
    finally:
        conn.close()

def get_embeddings_from_db():
    """Get all embeddings from the database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, filename, original_filename, page_numbers, title,
                       embedding_provider, embedding_model, created_at
                FROM embeddings
                ORDER BY created_at DESC
            """)
            embeddings = []
            for row in cur.fetchall():
                embedding = {
                    "id": row[0],
                    "filename": row[1],
                    "original_filename": row[2],
                    "page_numbers": row[3],
                    "title": row[4],
                    "embedding_provider": row[5],
                    "embedding_model": row[6],
                    "created_at": row[7]
                }
                embeddings.append(embedding)
            return embeddings
    except Exception as e:
        st.error(f"Error fetching embeddings: {e}")
        return []
    finally:
        conn.close()

def delete_document_from_db(doc_id):
    """Delete a document and its related data from the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Delete related embeddings first
            cur.execute("DELETE FROM embeddings WHERE chunk_id IN (SELECT id FROM document_chunks WHERE document_id = %s)", (doc_id,))
            # Delete related chunks
            cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (doc_id,))
            # Delete processing logs
            cur.execute("DELETE FROM processing_logs WHERE document_id = %s", (doc_id,))
            # Finally delete the document
            cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error deleting document: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_chunk_from_db(chunk_id):
    """Delete a chunk and its related embeddings from the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Delete related embeddings first
            cur.execute("DELETE FROM embeddings WHERE chunk_id = %s", (chunk_id,))
            # Delete the chunk
            cur.execute("DELETE FROM document_chunks WHERE id = %s", (chunk_id,))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error deleting chunk: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_embedding_from_db(embedding_id):
    """Delete an embedding from the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM embeddings WHERE id = %s", (embedding_id,))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error deleting embedding: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def insert_document_to_db(filename, file_path, file_size, file_type, content=None):
    """Insert a document into the database"""
    conn = get_db_connection()
    if not conn:
        st.error("❌ Cannot connect to database for document insertion")
        return False

    try:
        with conn.cursor() as cur:
            # Check if document already exists
            cur.execute("SELECT id, processed FROM documents WHERE filename = %s", (filename,))
            existing = cur.fetchone()

            if not existing:
                # Insert new document
                st.info(f"📄 Inserting new document: {filename}")
                cur.execute("""
                    INSERT INTO documents (filename, file_path, file_size, file_type, content, processed)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (filename, file_path, file_size, file_type, content, False))
                doc_id = cur.fetchone()[0]
                conn.commit()
                st.success(f"✅ Document '{filename}' inserted successfully (ID: {doc_id})")
                return True
            else:
                doc_id, was_processed = existing
                # Document already exists, update the record
                st.info(f"📄 Updating existing document: {filename}")
                cur.execute("""
                    UPDATE documents
                    SET file_path = %s, file_size = %s, file_type = %s, content = %s, processed = %s
                    WHERE filename = %s
                    RETURNING id
                """, (file_path, file_size, file_type, content, False, filename))
                updated_id = cur.fetchone()[0]
                conn.commit()
                st.success(f"✅ Document '{filename}' updated successfully (ID: {updated_id})")
                return True
    except Exception as e:
        st.error(f"❌ Error inserting document into database: {e}")
        st.error(f"File details - Name: {filename}, Path: {file_path}, Size: {file_size}, Type: {file_type}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_uploaded_document(uploaded_file):
    """Add uploaded document to session state, save to uploads folder, and insert into database"""
    if uploaded_file:
        # Save uploaded file to data directory
        data_dir = "data/uploads"
        os.makedirs(data_dir, exist_ok=True)
        upload_file_path = f"{data_dir}/{uploaded_file.name}"

        try:
            st.info(f"💾 Saving file to: {upload_file_path}")
            with open(upload_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Verify file was saved
            if not os.path.exists(upload_file_path):
                st.error(f"❌ Failed to save file: {upload_file_path}")
                return

            file_size = os.path.getsize(upload_file_path)
            st.success(f"✅ File saved successfully ({file_size} bytes)")

            # Read file content for text files
            content = None
            file_type = uploaded_file.name.split('.')[-1].lower()
            if file_type in ['txt', 'md', 'html']:
                try:
                    with open(upload_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    st.info(f"📄 Read {len(content)} characters of content")
                except Exception as e:
                    st.warning(f"⚠️ Could not read file content: {e}")
                    content = None

            # Insert document into database
            st.info("💾 Saving to database...")
            if insert_document_to_db(
                filename=uploaded_file.name,
                file_path=upload_file_path,
                file_size=file_size,
                file_type=file_type,
                content=content
            ):
                # Verify document was added to database
                documents = get_documents_from_db()
                if any(doc["filename"] == uploaded_file.name for doc in documents):
                    doc_info = {
                        "name": uploaded_file.name,
                        "size": f"{file_size / 1024:.1f} KB",
                        "upload_time": datetime.now().strftime("%H:%M:%S"),
                        "source_path": upload_file_path
                    }
                    st.session_state.uploaded_documents.append(doc_info)
                    st.success(f"🎉 File '{uploaded_file.name}' fully uploaded and verified in database!")

                    # Show database status
                    st.info(f"📊 Database now contains {len(documents)} documents")
                else:
                    st.error(f"❌ File saved locally but not found in database")
            else:
                st.error(f"❌ Failed to save file '{uploaded_file.name}' to database")

        except Exception as e:
            st.error(f"❌ Error saving file: {e}")
            st.error(f"File path: {upload_file_path}")

def update_extraction_source(source):
    """Update the source (URL or file path) in 1-extraction.py"""
    try:
        # For command line arguments, we don't need to modify the source code
        # The extraction script now uses argparse and takes the source as command line argument
        # We'll handle this by passing the source directly to the subprocess
        return True
    except Exception as e:
        st.error(f"Error updating extraction source: {e}")
        return False


import requests
import tempfile

def download_file(url):
    """Downloads a file from a URL and saves it to a temporary file."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        
        # Determine the file extension from the URL
        file_extension = os.path.splitext(url)[1]
        
        # Create a temporary file with the correct extension
        temp_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
        
        # Write the content to the temporary file
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        
        temp_file.close()
        return temp_file.name
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None

def run_extraction(source_path):
    """Run the extraction process with the given source path using selected provider"""
    st.write(f"Running extraction with source: {source_path}")  # Log the source path
    if source_path.startswith("http://") or source_path.startswith("https://"):
        st.write("Downloading file from URL...")
        downloaded_file = download_file(source_path)
        if downloaded_file:
            st.write(f"Downloaded file to: {downloaded_file}")
            source_path = downloaded_file
        else:
            st.error("Failed to download file from URL.")
            return False, "Failed to download file from URL."
    
    try:
        # Use database-based extraction for all providers
        extraction_provider = st.session_state.get("extraction_provider", "docling")
        
        if extraction_provider == "mistral":
            # Use unified extraction system with Mistral OCR preference
            cmd = [sys.executable, "1-extraction.py", "--source", source_path, "--prefer-cloud"]
        else:
            # Use unified extraction system with database processing
            cmd = [sys.executable, "1-extraction.py", "--process-db", "--mark-processed"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            timeout=300  # 5 minute timeout
        )
        
        # If Docling extraction fails, try Mistral OCR as fallback for scanned/Arabic documents
        if result.returncode != 0 and extraction_provider == "docling":
            st.warning("Docling extraction failed, trying unified system with Mistral OCR...")
            cmd = [sys.executable, "1-extraction.py", "--source", source_path, "--prefer-cloud"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding="utf-8",
                timeout=300
            )
        
        if result.returncode == 0:
            # For database-based extraction, we don't need to read a file
            # The content is stored directly in the database
            print(f"Extraction successful! Content stored in database.")
            return True, "Content extracted and stored in database successfully"
        else:
            error_msg = result.stderr or "Extraction failed"
            print(f"Extraction failed with error: {error_msg}")
            return False, error_msg
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def run_chunking():
    """Run the chunking process using database-based chunking"""
    try:
        st.info("🔪 Running chunking script: 2-chunking-neon.py")

        # Get current chunk count before processing
        chunks_before = get_chunks_from_db()
        chunks_before_count = len(chunks_before)

        result = subprocess.run(
            [sys.executable, "2-chunking-neon.py"],
            capture_output=True,
            encoding="utf-8",
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            st.success("✅ Chunking script completed successfully")

            # Check if chunks were actually created in database
            time.sleep(2)  # Give database time to update
            chunks_after = get_chunks_from_db()
            chunks_after_count = len(chunks_after)
            new_chunks = chunks_after_count - chunks_before_count

            if new_chunks > 0:
                st.success(f"✅ Chunking created {new_chunks} new chunks in database!")

                # Show details of new chunks
                recent_chunks = [c for c in chunks_after if c not in chunks_before]
                if recent_chunks:
                    st.info(f"📊 Recent chunks created:")
                    for chunk in recent_chunks[:3]:  # Show first 3
                        st.text(f"  • {chunk['filename']} (Chunk {chunk['chunk_index']})")
                    if len(recent_chunks) > 3:
                        st.text(f"  • ... and {len(recent_chunks) - 3} more chunks")
            else:
                st.warning("⚠️ Chunking completed but no new chunks found in database")
                st.info("💡 This might indicate the document was already chunked or an issue with database storage")

            return True, result.stdout
        else:
            st.error(f"❌ Chunking script failed (exit code: {result.returncode})")
            st.error(f"Script output: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        if "timed out" in str(e):
            st.error("⏰ Chunking timed out after 5 minutes")
            return False, "Chunking timed out after 5 minutes."
        st.error(f"💥 Unexpected error during chunking: {e}")
        return False, f"Unexpected error: {str(e)}"


def run_embedding():
    """Run the embedding process"""
    try:
        # Build command with API keys from session state
        cmd = [sys.executable, "3-embedding-neon.py"]

        # Add embedding provider argument
        embedding_provider = st.session_state.get("embedding_provider", "openai")
        cmd.extend(["--embedding-provider", embedding_provider])

        # Add API key arguments based on provider
        if embedding_provider == "openai":
            if st.session_state.openai_client:
                # Extract API key from the client
                api_key = st.session_state.openai_client.api_key
                cmd.extend(["--openai-api-key", api_key])
                st.info(f"🧬 Running embedding with OpenAI provider")
            else:
                return False, "❌ OpenAI client not configured"
        elif embedding_provider == "mistral":
            if st.session_state.mistral_client:
                # Extract API key from the client (Mistral stores it in sdk_configuration.security.api_key)
                api_key = st.session_state.mistral_client.sdk_configuration.security.api_key
                cmd.extend(["--mistral-api-key", api_key])
                st.info(f"🧬 Running embedding with Mistral provider")
            else:
                return False, "❌ Mistral client not configured"

        # Get current embedding count before processing
        embeddings_before = get_embeddings_from_db()
        embeddings_before_count = len(embeddings_before)

        result = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            cwd=os.getcwd(),
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            st.success("✅ Embedding script completed successfully")

            # Check if embeddings were actually created in database
            time.sleep(2)  # Give database time to update
            embeddings_after = get_embeddings_from_db()
            embeddings_after_count = len(embeddings_after)
            new_embeddings = embeddings_after_count - embeddings_before_count

            if new_embeddings > 0:
                st.success(f"✅ Embedding created {new_embeddings} new embeddings in database!")

                # Show details of new embeddings
                recent_embeddings = [e for e in embeddings_after if e not in embeddings_before]
                if recent_embeddings:
                    st.info(f"📊 Recent embeddings created:")
                    for embedding in recent_embeddings[:3]:  # Show first 3
                        st.text(f"  • {embedding['filename']} ({embedding['embedding_provider']})")
                    if len(recent_embeddings) > 3:
                        st.text(f"  • ... and {len(recent_embeddings) - 3} more embeddings")
            else:
                st.warning("⚠️ Embedding completed but no new embeddings found in database")
                st.info("💡 This might indicate all chunks were already embedded or an issue with database storage")

            return True, result.stdout
        else:
            st.error(f"❌ Embedding script failed (exit code: {result.returncode})")
            st.error(f"Script output: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        if "timed out" in str(e):
            st.error("⏰ Embedding timed out after 5 minutes")
            return False, "Embedding timed out after 5 minutes."
        st.error(f"💥 Unexpected error during embedding: {e}")
        return False, f"Unexpected error: {str(e)}"


def get_embedding(text):
    """Get embedding for text using configured provider"""
    if embedding_provider == "openai":
        client = st.session_state.openai_client
        if not client:
            raise ValueError("OpenAI client not configured")
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding
    elif embedding_provider == "mistral":
        client = st.session_state.mistral_client
        if not client:
            raise ValueError("Mistral client not configured")
        response = client.embeddings.create(
            model="mistral-embed",
            inputs=[text]
        )
        return response.data[0].embedding

def search_embeddings(query, top_k=3):
    """Search through stored embeddings for similar content using ONLY Neon database"""
    # Use ONLY Neon database - no JSON fallback
    neon_results = search_embeddings_neon(query, top_k)
    
    if not neon_results:
        # Check if database has any embeddings for this provider
        if not check_database_has_embeddings(embedding_provider):
            st.error(f"❌ No embeddings found in Neon database for provider: {embedding_provider}")
            st.error(f"Please run 3-embedding-neon.py with --embedding-provider {embedding_provider} first.")
        else:
            st.warning("⚠️ No matching embeddings found for your query in the Neon database.")
    
    return neon_results

def get_context(query: str, source_file: str) -> str:
    """Get relevant context from embeddings based on user query using ONLY Neon database.

    Args:
        query: User's question for semantic search
        source_file: Path to the source file (not used for fallback - kept for API compatibility)

    Returns:
        str: Relevant context from Neon database embeddings
    """
    try:
        st.write(f"🔍 Searching for context related to: '{query}'")

        # Check if embeddings exist in database first
        if not check_database_has_embeddings(embedding_provider):
            st.error(f"❌ No embeddings found in database for provider '{embedding_provider}'")
            st.error("Please run the embedding process first using the sidebar: Extract → Chunk → Embed")
            return ""

        # Use ONLY Neon database for semantic search
        results = search_embeddings(query, top_k=3)

        if results:
            # Build context from top results
            context_parts = []
            for i, (score, result) in enumerate(results, 1):
                context_parts.append(f"Relevant section {i} (similarity: {score:.3f}):")
                context_parts.append(result["text"])
                context_parts.append("---")

            context = "\n".join(context_parts)
            st.success(f"✅ Found {len(results)} relevant sections using Neon database embeddings")
            return context
        else:
            st.warning("⚠️ No relevant embeddings found in Neon database for your query.")
            st.info("This could be because:")
            st.info("• No documents have been processed yet")
            st.info("• The query doesn't match any content in your documents")
            st.info("• Embeddings haven't been generated for the current provider")
            return ""

    except Exception as e:
        st.error(f"❌ Error retrieving context from Neon database: {str(e)}")
        import traceback
        st.error(f"Full traceback: {traceback.format_exc()}")
        return ""


def get_chat_response(messages, context: str) -> str:
    """Get response from the selected LLM API.

    Args:
        messages: Chat history
        context: Retrieved context from database

    Returns:
        str: Model's response
    """
    system_prompt = f"""You are a helpful assistant that answers questions based on the provided context.
    Use only the information from the context to answer questions. If you're unsure or the context
    doesn't contain the relevant information, say so. Don't make up answers or use prior knowledge. Answer same in the document.
    Context:
    {context}
    """

    messages_with_context = [{"role": "system", "content": system_prompt}, *messages]

    if llm_provider == "openai":
        # Create the response with OpenAI (non-streaming for better container compatibility)
        client = st.session_state.openai_client
        if not client:
            raise ValueError("OpenAI client not configured")
        response = client.chat.completions.create(
            model=st.session_state.get("openai_model", "gpt-4o-mini"),
            messages=messages_with_context,
            temperature=0.7,
        )
        return response.choices[0].message.content

    elif llm_provider == "mistral":
        # Create the response with Mistral (non-streaming for better container compatibility)
        client = st.session_state.mistral_client
        if not client:
            raise ValueError("Mistral client not configured")
        response = client.chat.completions.create(
            model=st.session_state.get("mistral_model", "mistral-large-latest"),
            messages=messages_with_context,
            temperature=0.7,
        )
        return response.choices[0].message.content


# Initialize Streamlit app with custom styling
st.set_page_config(
    page_title="📚 Document Q&A Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2.5rem;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 200%;
        border-radius: 25px;
        color: white;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
        animation: gradientShift 4s ease-in-out infinite;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transform: rotate(45deg);
        animation: shimmer 3s ease-in-out infinite;
    }
    @keyframes shimmer {
        0% {
            transform: translateX(-100%) translateY(-100%) rotate(45deg);
        }
        100% {
            transform: translateX(100%) translateY(100%) rotate(45deg);
        }
    }
    .sidebar-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #3498db;
        background: linear-gradient(90deg, #3498db, #2980b9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .upload-section {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px dashed #6c757d;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .button-primary {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 15px !important;
        padding: 1rem 2rem !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        font-size: 1rem !important;
    }
    .button-primary::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }
    .button-primary:hover::before {
        left: 100%;
    }
    .button-primary:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4) !important;
    }
    .button-primary:active {
        transform: translateY(-1px) scale(0.98) !important;
    }
    .button-secondary {
        background: linear-gradient(45deg, #6c757d, #495057) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        border-radius: 15px !important;
        padding: 1rem 2rem !important;
        box-shadow: 0 6px 20px rgba(108, 117, 125, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        font-size: 1rem !important;
    }
    .button-secondary::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }
    .button-secondary:hover::before {
        left: 100%;
    }
    .button-secondary:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 12px 30px rgba(108, 117, 125, 0.4) !important;
    }
    .button-secondary:active {
        transform: translateY(-1px) scale(0.98) !important;
    }
    .chat-container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 2rem;
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        min-height: 600px;
        max-height: 700px;
        margin-bottom: 2rem;
        display: flex;
        flex-direction: column;
        position: relative;
        backdrop-filter: blur(10px);
    }
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        padding-right: 1.5rem;
        margin-bottom: 1rem;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .chat-messages::-webkit-scrollbar {
        width: 12px;
    }
    .chat-messages::-webkit-scrollbar-track {
        background: linear-gradient(180deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        margin: 0.5rem;
    }
    .chat-messages::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #c1c1c1, #a8a8a8);
        border-radius: 10px;
        border: 2px solid #f8f9fa;
        transition: all 0.3s ease;
    }
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #a8a8a8, #8e8e8e);
        transform: scale(1.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        margin-bottom: 2.5rem;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        border-radius: 15px 15px 0px 0px;
        gap: 2px;
        padding: 15px 25px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.8);
        position: relative;
        overflow: hidden;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(145deg, #e9ecef, #dee2e6);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        color: white !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        transform: translateY(-2px);
    }
    .status-success {
        background: linear-gradient(145deg, #d4edda, #c3e6cb) !important;
        border-color: #28a745 !important;
        color: #155724 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    .status-error {
        background: linear-gradient(145deg, #f8d7da, #f5c6cb) !important;
        border-color: #dc3545 !important;
        color: #721c24 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    .stChatMessage {
        border-radius: 20px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .stChatMessage::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        opacity: 0.8;
    }
    .stChatMessage[data-testid="stChatMessage-user"] {
        background: linear-gradient(145deg, #e8f4fd, #b3d9ff) !important;
        border-left: 5px solid #2196f3 !important;
        animation: slideInRight 0.5s ease-out !important;
    }
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        background: linear-gradient(145deg, #f8f0ff, #e9d4ff) !important;
        border-left: 5px solid #9c27b0 !important;
        animation: slideInLeft 0.5s ease-out !important;
    }
    .stChatMessage:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12) !important;
    }
    .stChatInput {
        max-width: 1000px !important;
        margin: 0 auto !important;
        border-radius: 30px !important;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15) !important;
        border: 2px solid rgba(255, 255, 255, 0.8) !important;
        background: linear-gradient(145deg, #ffffff, #f8f9fa) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .stChatInput:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25) !important;
        transform: translateY(-2px) !important;
    }
    .stChatInput::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
        transition: left 0.5s ease;
    }
    .stChatInput:focus-within::before {
        left: 100%;
    }
    .welcome-section {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 3rem;
        border-radius: 25px;
        margin-bottom: 3rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.08);
        border: 1px solid rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .welcome-section::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        background-size: 200% 100%;
        animation: gradientShift 3s ease-in-out infinite;
    }
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    @keyframes gradientShift {
        0%, 100% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
    }
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.2rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        .chat-container {
            padding: 1rem;
            min-height: 500px;
            max-height: 600px;
            margin-bottom: 1rem;
        }
        .chat-messages {
            padding: 0.75rem;
            padding-right: 1rem;
        }
        .stChatInput {
            max-width: 100% !important;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 10px 15px;
            font-size: 1rem;
        }
        .button-primary, .button-secondary {
            padding: 0.75rem 1.5rem !important;
            font-size: 0.9rem !important;
        }
        .welcome-section {
            padding: 2rem 1.5rem;
        }
    }
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.8rem;
            padding: 1rem;
        }
        .chat-container {
            padding: 0.75rem;
            border-radius: 15px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            margin-bottom: 1.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            padding: 8px 12px;
            font-size: 0.9rem;
        }
    }
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .chat-container {
            background: linear-gradient(145deg, #2d3748, #1a202c);
            border-color: #4a5568;
        }
        .chat-messages {
            background: rgba(45, 55, 72, 0.5);
            border-color: rgba(74, 85, 104, 0.3);
        }
        .stChatInput {
            background: linear-gradient(145deg, #2d3748, #1a202c) !important;
            border-color: rgba(74, 85, 104, 0.5) !important;
        }
    }
    /* Accessibility improvements */
    .stChatMessage:focus {
        outline: 2px solid #667eea;
        outline-offset: 2px;
    }
    .button-primary:focus, .button-secondary:focus {
        outline: 2px solid #667eea;
        outline-offset: 2px;
    }
    /* Loading animation */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    </style>
""", unsafe_allow_html=True)
# Sidebar for document processing
with st.sidebar:
    st.markdown('<div class="sidebar-header">📄 Document Processing</div>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📁 Upload Document")
    uploaded_file = st.file_uploader(
        "Drag & drop or click to upload",
        type=["pdf", "docx", "xlsx", "pptx", "md", "html", "htm", "xhtml", "png", "jpg", "jpeg", "tiff", "bmp"],
        help="Upload a document for processing (PDF, DOCX, XLSX, PPTX, Markdown, HTML, Images)",
        label_visibility="collapsed"
    )
    
    # Add upload button
    if uploaded_file is not None:
        if st.button("📤 Add to Uploaded Documents", use_container_width=True):
            # Check if this file is already in the uploaded documents
            if not any(doc["name"] == uploaded_file.name for doc in st.session_state.uploaded_documents):
                add_uploaded_document(uploaded_file)
                st.rerun()
            else:
                st.warning("⚠️ File already uploaded")
    
    st.subheader("🔗 Or enter URL")
    url = st.text_input(
        "Document URL",
        placeholder="https://example.com/document.pdf",
        help="Enter URL to document or webpage (PDF, DOCX, HTML, etc.)",
        label_visibility="collapsed"
    )
    
    if url:
        if st.button("📥 Add URL Document", use_container_width=True):
            # Download the file from the URL
            downloaded_file = download_file(url)
            if downloaded_file:
                # Extract filename from path
                file_name = os.path.basename(downloaded_file)
                
                # Move file to uploads directory
                data_dir = "data/uploads"
                os.makedirs(data_dir, exist_ok=True)
                upload_file_path = os.path.join(data_dir, file_name)
                
                try:
                    os.rename(downloaded_file, upload_file_path)
                    
                    # Get file size and upload time
                    file_size = os.path.getsize(upload_file_path)
                    upload_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Read file content for text files
                    content = None
                    file_type = file_name.split('.')[-1].lower()
                    if file_type in ['txt', 'md', 'html']:
                        try:
                            with open(upload_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except:
                            content = None
                    
                    # Insert document into database
                    if insert_document_to_db(
                        filename=file_name,
                        file_path=upload_file_path,
                        file_size=file_size,
                        file_type=file_type,
                        content=content
                    ):
                        # Create doc_info dictionary
                        doc_info = {
                            "name": file_name,
                            "size": f"{file_size / 1024:.1f} KB",
                            "upload_time": upload_time,
                            "source_path": upload_file_path
                        }
                        
                        # Add to session state
                        st.session_state.uploaded_documents.append(doc_info)
                        st.success(f"✅ File '{file_name}' downloaded and added successfully to database!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add file '{file_name}' to database")
                except Exception as e:
                    st.error(f"Error moving file: {e}")
            else:
                st.error("Failed to download file from URL.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display uploaded documents in sidebar
    st.markdown('<div class="sidebar-header">📁 Uploaded Documents</div>', unsafe_allow_html=True)
    
    if st.session_state.uploaded_documents:
        for i, doc_info in enumerate(st.session_state.uploaded_documents):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{doc_info['name']}**")
                st.caption(f"Size: {doc_info['size']} • Uploaded: {doc_info['upload_time']}")
            with col2:
                if st.button("🗑️", key=f"delete_{i}"):
                    # Remove document from session state and delete the file
                    doc_info = st.session_state.uploaded_documents[i]
                    try:
                        if os.path.exists(doc_info["source_path"]):
                            os.remove(doc_info["source_path"])
                        del st.session_state.uploaded_documents[i]
                        st.success(f"✅ File '{doc_info['name']}' deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting file: {e}")
    else:
        st.info("📝 No documents uploaded yet")
    
    st.markdown("---")
    
    # Display current LLM, embedding, and extraction providers
    if llm_provider == "openai":
        openai_model = st.session_state.get("openai_model", "gpt-4o-mini")
        st.info(f"💬 Chat: OpenAI ({openai_model})")
    elif llm_provider == "mistral":
        mistral_model = st.session_state.get("mistral_model", "mistral-large-latest")
        st.info(f"💬 Chat: Mistral ({mistral_model})")
    
    # Display embedding provider
    if embedding_provider == "openai":
        st.info(f"🧬 Embeddings: OpenAI (text-embedding-3-large)")
    elif embedding_provider == "mistral":
        st.info(f"🧬 Embeddings: Mistral (mistral-embed)")
    
    # Display extraction provider
    extraction_provider = st.session_state.get("extraction_provider", "docling")
    if extraction_provider == "docling":
        st.info(f"📄 Extraction: Docling (local)")
    elif extraction_provider == "mistral":
        st.info(f"📄 Extraction: Mistral OCR (cloud)")
    
    # Add settings button to reconfigure
    if st.button("⚙️ Change LLM Provider", use_container_width=True):
        # Clear all configuration
        st.session_state.api_keys_configured = False
        st.session_state.openai_client = None
        st.session_state.mistral_client = None
        st.session_state.embedding_provider = "openai"
        st.session_state.messages = []  # Clear chat history
        st.rerun()
    
    st.markdown("---")
    
    # File selection for extraction
    if st.session_state.uploaded_documents:
        file_options = [doc["name"] for doc in st.session_state.uploaded_documents]
        selected_file = st.selectbox(
        
            "📄 Select file to process:",
            options=file_options,
            help="Choose which uploaded file you want to extract"
        )
    
    # Processing buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        extract_btn = st.button("🚀 Extract", use_container_width=True, type="primary")
    
    with col2:
        fast_split_btn = st.button("⚡ Fast Split Only", use_container_width=True, type="primary")

    with col3:
        chunk_btn = st.button("🔪 Chunk", use_container_width=True, type="secondary")
    
    embed_btn = st.button("🧬 Embed", use_container_width=True, type="secondary")

    # Fast splitting only
    if fast_split_btn:
        if st.session_state.uploaded_documents:
            selected_doc = next((doc for doc in st.session_state.uploaded_documents if doc["name"] == selected_file), None)
            if selected_doc:
                source_to_use = selected_doc["source_path"]
                with st.status("⚡ Fast splitting file...", expanded=True) as status:
                    st.write(f"Fast splitting {source_to_use} with fast_split_only.py")
                    try:
                        result = subprocess.run(
                            [sys.executable, "fast_split_only.py", source_to_use],
                            capture_output=True,
                            encoding="utf-8",
                            timeout=300  # 5 minute timeout
                        )
                        if result.returncode == 0:
                            st.write("✅ Fast splitting completed successfully!")
                            st.code(result.stdout, language="text")
                            status.update(label="✅ Fast Splitting Complete!", state="complete")
                            st.balloons()
                            
                            # Auto-refresh to show new chunk files
                            st.rerun()
                        else:
                            st.error("❌ Fast splitting failed")
                            st.code(result.stderr, language="text")
                            status.update(label="❌ Fast Splitting Failed", state="error")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        status.update(label="❌ Error", state="error")
            else:
                st.error("❌ Selected file not found")
        else:
            st.warning("📝 Please upload a document file first")
    
    # Process extraction
    if extract_btn:
        if st.session_state.uploaded_documents:
            # Get the selected file path
            selected_doc = next((doc for doc in st.session_state.uploaded_documents if doc["name"] == selected_file), None)
            if selected_doc:
                source_to_use = selected_doc["source_path"]
                st.session_state["source_to_use"] = source_to_use
                
                with st.status("🔄 Processing extraction...", expanded=True) as status:
                    # Update the extraction source
                    st.write("📝 Updating extraction script...")
                    if update_extraction_source(source_to_use):
                        st.write("✅ Extraction script updated")
                        
                        # Run the extraction process
                        st.write("🔍 Extracting document content...")
                        success, output = run_extraction(source_to_use)
                        
                        if success:
                            st.write("✅ Extraction completed successfully!")
                            st.code(output, language="text")
                            status.update(label="✅ Extraction Complete!", state="complete")
                            st.session_state["extraction_successful"] = True
                            st.balloons()
                            st.success("Document ready for questions! 🎉")
                            
                            # Auto-refresh to show updated state
                            st.rerun()
                        else:
                            st.error("❌ Extraction failed")
                            st.code(output, language="text")
                            status.update(label="❌ Extraction Failed", state="error")
                    else:
                        st.error("Failed to update extraction script")
                        status.update(label="❌ Update Failed", state="error")
            else:
                st.error("❌ Selected file not found")
        else:
            st.warning("📝 Please upload a document file first")
    
    # Process chunking
    if chunk_btn:
        if not st.session_state.uploaded_documents:
            st.warning("📝 Please upload a document first")
        else:
            selected_doc = next((doc for doc in st.session_state.uploaded_documents if doc["name"] == selected_file), None)
            if not selected_doc:
                st.warning("⚠️ Please select a file to process first")
            else:
                with st.status("🔄 Processing chunking...", expanded=True) as status:
                    st.write(f"🔪 Chunking document: {selected_doc['name']}")
                    st.write(f"File path: {selected_doc['source_path']}")

                    # Check if file exists before processing
                    if not os.path.exists(selected_doc['source_path']):
                        st.error(f"❌ File not found: {selected_doc['source_path']}")
                        status.update(label="❌ File Not Found", state="error")
                    else:
                        success, output = run_chunking()
                        st.session_state["chunking_successful"] = False

                        if success:
                            st.write("✅ Chunking completed successfully!")
                            st.code(output, language="text")

                            # Check if chunks were actually created in database
                            time.sleep(1)  # Brief pause to let database update
                            chunks = get_chunks_from_db()
                            chunk_count = len(chunks)

                            if chunk_count > 0:
                                st.success(f"✅ Chunking created {chunk_count} chunks in database!")
                                status.update(label=f"✅ Chunking Complete! ({chunk_count} chunks)", state="complete")
                                st.session_state["chunking_successful"] = True
                                st.balloons()

                                # Show recent chunks
                                recent_chunks = [c for c in chunks if c["filename"] == selected_doc["name"]]
                                if recent_chunks:
                                    st.info(f"📊 Created {len(recent_chunks)} chunks for '{selected_doc['name']}'")
                            else:
                                st.warning("⚠️ Chunking completed but no chunks found in database")
                                st.info("This might indicate an issue with database storage. Check the output above for errors.")
                                status.update(label="⚠️ Chunking Completed (No DB Update)", state="complete")

                            # Auto-refresh to show updated state
                            st.rerun()
                        else:
                            st.error("❌ Chunking failed")
                            st.code(output, language="text")
                            status.update(label="❌ Chunking Failed", state="error")

                            # Show troubleshooting tips
                            with st.expander("🔧 Troubleshooting Tips", expanded=True):
                                st.markdown("""
                                **Common chunking issues:**

                                1. **File not found**: Make sure the file exists at the specified path
                                2. **Database connection**: Check if NEON_CONNECTION_STRING is set correctly
                                3. **Script errors**: Check the error output above for specific issues
                                4. **Dependencies**: Ensure all required packages are installed

                                **Debug steps:**
                                - Check if the file exists: `{selected_doc['source_path']}`
                                - Verify database connection string in .env file
                                - Try running the script manually: `python 2-chunking-neon.py`
                                """)
    
    # Process embedding
    if embed_btn:
        with st.status("🔄 Processing embedding...", expanded=True) as status:
            st.write("🧬 Creating embeddings...")
            success, output = run_embedding()
            
            if success:
                st.write("✅ Embedding completed successfully!")
                st.code(output, language="text")
                status.update(label="✅ Embedding Complete!", state="complete")
                st.success("Embeddings created successfully! 🎯")
                
                # Auto-refresh to show updated state
                st.rerun()
            else:
                st.error("❌ Embedding failed")
                st.code(output, language="text")
                status.update(label="❌ Embedding Failed", state="error")
    
    
    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Main content area with tabs
st.markdown('<div class="main-header">📚 Document Q&A Assistant</div>', unsafe_allow_html=True)

# Chat input - placed above tabs so responses appear above input
st.markdown("### 💬 Ask Questions About Your Documents")
chat_input_container = st.container()
with chat_input_container:
    if prompt := st.chat_input("💬 Ask a question about the document...", key="chat_input"):
        # Add user message to chat history first
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get relevant context using embeddings
        with st.status("🔍 Searching embeddings and generating response...", expanded=False) as status:
            try:
                # For embeddings, we don't need the source file - use empty string
                context = get_context(prompt, "")

                if context:
                    # Add assistant response to chat history
                    response = get_chat_response(st.session_state.messages, context)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    status.update(label="✅ Response Generated!", state="complete")
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "I'm sorry, I couldn't find any relevant information in your documents to answer your question. Please make sure your documents have been processed (Extract → Chunk → Embed) and try again."})
                    status.update(label="❌ No Context Found", state="error")

            except Exception as e:
                error_msg = f"I encountered an error while processing your question: {str(e)}"
                st.error(f"❌ Error: {error_msg}")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                status.update(label="❌ Error Occurred", state="error")

        # Rerun to update the chat display
        st.rerun()

# Create tabs for Chat and Database Management
tab1, tab2 = st.tabs(["💬 Chat", "🗃️ Database Management"])

# Tab 1: Chat Interface
with tab1:
    # Simple chat interface without complex containers
    chat_container = st.container()

    with chat_container:
        # Messages area - using Streamlit's native chat components for better layout
        if st.session_state.messages:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        else:
            # Simple empty state without complex styling
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #6c757d; background: rgba(102, 126, 234, 0.05); border-radius: 10px; border: 1px solid rgba(102, 126, 234, 0.1);">
                <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.7;">💬</div>
                <h3 style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #667eea;">Start a conversation</h3>
                <p style="font-size: 1rem; margin: 0 auto; line-height: 1.6; color: #6c757d;">Ask questions about your documents using the chat input above.</p>
            </div>
            """, unsafe_allow_html=True)

# Tab 2: Database Management
with tab2:
    st.markdown("### 🗃️ Database Management")

    # Add refresh, verification, sync, and debug buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🔍 Verify DB", use_container_width=True):
            with st.spinner("Checking database integrity..."):
                issues = verify_database_integrity()
                if not issues:
                    st.success("✅ Database integrity check passed!")
                else:
                    for issue in issues:
                        st.warning(issue)
    with col3:
        if st.button("🔄 Sync Files", use_container_width=True):
            with st.spinner("Syncing local files to database..."):
                synced_count = sync_local_files_to_database()
                if synced_count > 0:
                    st.success(f"✅ Synced {synced_count} files to database!")
                    st.rerun()
                else:
                    st.info("ℹ️ All local files are already in database")
    with col4:
        if st.button("🐛 Debug DB", use_container_width=True):
            with st.spinner("Analyzing database content..."):
                debug_info = debug_database_content()
                st.code(debug_info, language="text")

    # Add direct database check
    st.markdown("#### 🔍 Direct Database Check")
    if st.button("🔍 Check Neon DB Contents", type="secondary", use_container_width=True):
        with st.spinner("Querying Neon database..."):
            debug_info = debug_database_content()
            st.markdown(debug_info)

            # Also show a summary
            if "❌ Cannot connect" in debug_info:
                st.error("❌ Cannot connect to your Neon database. Check your NEON_CONNECTION_STRING.")
            elif "embeddings: 0 records" in debug_info:
                st.warning("⚠️ No embeddings found in database. Run embedding process to create them.")
            elif "embeddings:" in debug_info and "0 records" not in debug_info:
                st.success("✅ Embeddings found in database!")

    # Get database information
    documents = get_documents_from_db()
    chunks = get_chunks_from_db()
    embeddings = get_embeddings_from_db()

    # Show processing status and guidance
    if documents:
        processed_docs = [doc for doc in documents if doc["processed"]]
        unprocessed_docs = [doc for doc in documents if not doc["processed"]]

        if unprocessed_docs:
            st.warning(f"⚠️ **Processing Required**: {len(unprocessed_docs)} of {len(documents)} documents need processing")

            with st.expander("📋 Documents Needing Processing", expanded=True):
                for doc in unprocessed_docs:
                    st.markdown(f"""
                    **📄 {doc["filename"]}** ⏳<br>
                    <small>Size: {doc["file_size"]/1024:.1f} KB | Uploaded: {doc["upload_date"]}</small><br>
                    <small>Status: Needs Extraction → Chunking → Embedding</small>
                    """, unsafe_allow_html=True)

                    if st.button("🚀 Process Document", key=f"process_{doc['id']}", help=f"Start processing {doc['filename']}"):
                        st.info(f"💡 Use the sidebar to process '{doc['filename']}' with: Extract → Chunk → Embed")
                        st.session_state.selected_file = doc["filename"]

            if processed_docs:
                st.success(f"✅ **{len(processed_docs)} documents** are fully processed and ready for questions!")

        # Create columns for different database views
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📄 All Documents")
            for doc in documents:
                status_icon = "✅" if doc["processed"] else "⏳"
                status_text = "Processed" if doc["processed"] else "Unprocessed"
                st.markdown(f"""
                **{doc["filename"]}** {status_icon}<br>
                <small>Size: {doc["file_size"]/1024:.1f} KB | Status: {status_text} | Uploaded: {doc["upload_date"]}</small>
                """, unsafe_allow_html=True)

                if not doc["processed"]:
                    st.info("💡 Process this document using sidebar: Extract → Chunk → Embed")
                else:
                    # Check if document has chunks
                    doc_chunks = [c for c in chunks if c["filename"] == doc["filename"]]
                    has_chunks = len(doc_chunks) > 0

                    if has_chunks:
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                        with col_btn1:
                            if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}", help=f"Delete {doc['filename']}"):
                                if delete_document_from_db(doc["id"]):
                                    st.success(f"✅ Document '{doc['filename']}' deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete document '{doc['filename']}'")
                        with col_btn2:
                            if st.button("📋 Chunks", key=f"chunks_{doc['id']}", help=f"View chunks for {doc['filename']}"):
                                st.session_state.selected_doc_for_chunks = doc["id"]
                        with col_btn3:
                            if st.button("🔍 Embeddings", key=f"embeddings_{doc['id']}", help=f"View embeddings for {doc['filename']}"):
                                st.session_state.selected_doc_for_embeddings = doc["id"]
                    else:
                        # Document is marked as processed but has no chunks
                        st.warning(f"⚠️ Document marked as processed but has no chunks")
                        col_btn1, col_btn2 = st.columns([1, 1])
                        with col_btn1:
                            if st.button("🔄 Reset", key=f"reset_doc_{doc['id']}", help=f"Reset {doc['filename']} for reprocessing"):
                                if reset_document_for_reprocessing(doc["id"]):
                                    st.success(f"✅ Document '{doc['filename']}' reset for reprocessing!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to reset document '{doc['filename']}'")
                        with col_btn2:
                            if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}", help=f"Delete {doc['filename']}"):
                                if delete_document_from_db(doc["id"]):
                                    st.success(f"✅ Document '{doc['filename']}' deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete document '{doc['filename']}'")
                st.markdown("---")
    else:
        st.info("📝 No documents found in database - upload documents using the sidebar first")

    with col2:
        st.markdown("#### 🔪 Document Chunks")
        if chunks:
            st.success(f"✅ Found {len(chunks)} chunks from processed documents")

            # Group chunks by document
            chunks_by_doc = {}
            for chunk in chunks:
                doc_name = chunk["filename"]
                if doc_name not in chunks_by_doc:
                    chunks_by_doc[doc_name] = []
                chunks_by_doc[doc_name].append(chunk)

            # Show chunks for each document
            for doc_name, doc_chunks in chunks_by_doc.items():
                with st.expander(f"📄 {doc_name} ({len(doc_chunks)} chunks)", expanded=False):
                    for chunk in doc_chunks[:5]:  # Show first 5 chunks per document
                        st.markdown(f"""
                        **Chunk {chunk["chunk_index"]}**<br>
                        <small>Tokens: {chunk["token_count"]} | Type: {chunk["chunk_type"]}</small><br>
                        <small>Preview: {chunk["chunk_text"][:150]}...</small>
                        """, unsafe_allow_html=True)

                        if st.button("🗑️ Delete Chunk", key=f"del_chunk_{chunk['id']}", help=f"Delete chunk {chunk['chunk_index']}"):
                            if delete_chunk_from_db(chunk["id"]):
                                st.success(f"✅ Chunk {chunk['chunk_index']} deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete chunk {chunk['chunk_index']}")

                        st.markdown("---")
                    if len(doc_chunks) > 5:
                        st.info(f"📊 Showing 5 of {len(doc_chunks)} chunks for {doc_name}")
        else:
            if documents and not any(doc["processed"] for doc in documents):
                st.warning("⚠️ No chunks found - documents need to be processed first")
                st.info("💡 Use the sidebar to run: Extract → Chunk → Embed on your uploaded documents")
            else:
                st.info("🔪 No chunks found in database")

    # Embeddings section (full width)
    st.markdown("#### 🧬 Embeddings")
    if embeddings:
        st.success(f"✅ Found {len(embeddings)} embeddings from processed documents")

        # Group embeddings by document
        embeddings_by_doc = {}
        for embedding in embeddings:
            doc_name = embedding["filename"]
            if doc_name not in embeddings_by_doc:
                embeddings_by_doc[doc_name] = []
            embeddings_by_doc[doc_name].append(embedding)

        # Show embeddings for each document
        for doc_name, doc_embeddings in embeddings_by_doc.items():
            with st.expander(f"📄 {doc_name} ({len(doc_embeddings)} embeddings)", expanded=False):
                for embedding in doc_embeddings[:5]:  # Show first 5 embeddings per document
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"""
                        **{embedding["filename"]}**<br>
                        <small>Provider: {embedding["embedding_provider"]} | Model: {embedding["embedding_model"]}</small><br>
                        <small>Created: {embedding["created_at"]}</small>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_emb_{embedding['id']}", help=f"Delete embedding for {embedding['filename']}"):
                            if delete_embedding_from_db(embedding["id"]):
                                st.success(f"✅ Embedding for '{embedding['filename']}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete embedding for '{embedding['filename']}'")
                if len(doc_embeddings) > 5:
                    st.info(f"📊 Showing 5 of {len(doc_embeddings)} embeddings for {doc_name}")
    else:
        if chunks:
            st.warning("⚠️ No embeddings found - documents have been chunked but not embedded yet")
            st.info("💡 Use the sidebar to run: Embed on your chunked documents")
        elif documents and any(doc["processed"] for doc in documents):
            st.warning("⚠️ No embeddings found - documents are processed but not embedded")
            st.info("💡 Use the sidebar to run: Embed on your processed documents")
        else:
            st.info("🧬 No embeddings found in database")

    # Database statistics
    st.markdown("#### 📊 Database Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        doc_count = len(documents)
        st.metric("Documents", doc_count)

    with col2:
        chunk_count = len(chunks)
        st.metric("Chunks", chunk_count)

    with col3:
        embedding_count = len(embeddings)
        st.metric("Embeddings", embedding_count)

    with col4:
        # Calculate total size
        total_size = sum(doc["file_size"] for doc in documents) if documents else 0
        st.metric("Total Size", f"{total_size/1024/1024:.1f} MB")

    # Processing status summary
    if documents:
        st.markdown("#### 📈 Processing Status Summary")
        total_docs = len(documents)
        processed_docs = len([doc for doc in documents if doc["processed"]])

        if total_docs > 0:
            progress = processed_docs / total_docs
            st.progress(progress, text=f"Document Processing: {processed_docs}/{total_docs} completed")

            if processed_docs == 0:
                st.info("🚀 **Next Steps**: Use the sidebar to process your documents: Extract → Chunk → Embed")
            elif processed_docs < total_docs:
                st.warning(f"⚡ **{total_docs - processed_docs} documents** still need processing")
            else:
                st.success("🎉 **All documents are fully processed** and ready for questions!")

