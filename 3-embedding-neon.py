import argparse
from typing import List, Dict, Optional
import json
import os
import glob
import sys
import warnings
import psycopg2
from psycopg2.extras import Json
import numpy as np
import time
import logging
import signal
import pickle
import threading
from datetime import datetime, timedelta

from docling.chunking import HierarchicalChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from openai import OpenAI
from mistralai import Mistral

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding_process.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants for robust large file handling
EMBEDDING_TIMEOUT = 1800  # 30 minutes timeout per chunk (increased from 15 minutes)
MAX_RETRIES = 8  # Maximum retries per chunk (increased from 5)
RETRY_DELAY = 15  # Delay between retries in seconds (increased from 10)
RATE_LIMIT_DELAY = 3  # Delay between API calls to avoid rate limits (increased from 2)
PROCESSING_TIMEOUT = 14400  # 4 hour overall timeout for the entire process (increased from 2 hours)
PROGRESS_SAVE_INTERVAL = 3  # Save progress every 3 chunks (decreased from 5)
CHECKPOINT_FILE = 'embedding_checkpoint.pkl'

# Chunk size optimization for large files
MAX_CHUNK_SIZE = 4000  # Reduced maximum tokens per chunk for better timeout handling
OPTIMAL_CHUNK_SIZE = 2000  # Reduced optimal tokens per chunk for large files
EMERGENCY_CHUNK_SIZE = 1000  # Emergency chunk size for problematic files

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate embeddings for document chunks and store in Neon database')
parser.add_argument('--embedding-provider', type=str, default=None,
                    help='Embedding provider: openai or mistral')
parser.add_argument('--openai-api-key', type=str, default=None,
                    help='OpenAI API key (required if using OpenAI)')
parser.add_argument('--mistral-api-key', type=str, default=None,
                    help='Mistral API key (required if using Mistral)')
parser.add_argument('--resume', action='store_true',
                    help='Resume from previous checkpoint if available')
parser.add_argument('--batch-size', type=int, default=1,
                    help='Number of chunks to process before saving progress (default: 1)')
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
    logger.info("Using OpenAI for embeddings")
elif embedding_provider == "mistral":
    # Get API key - command line args take precedence over env vars
    api_key = args.mistral_api_key or os.getenv("MISTRAL_API_KEY")
    if not api_key:
        logger.error("Mistral API key is required. Provide it via --mistral-api-key argument or MISTRAL_API_KEY environment variable.")
        exit(1)
    mistral_client = Mistral(api_key=api_key)
    logger.info("Using Mistral for embeddings")
else:
    logger.error("Invalid EMBEDDING_PROVIDER. Use 'openai' or 'mistral'")
    exit(1)

MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

# Initialize DocumentConverter
converter = DocumentConverter()

# Global variables for progress tracking
processed_chunks = set()
failed_chunks = set()
start_time = None
last_progress_save = 0

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def save_checkpoint(chunks, processed_chunks, failed_chunks, current_index):
    """Save processing progress to checkpoint file"""
    checkpoint_data = {
        'processed_chunks': list(processed_chunks),
        'failed_chunks': list(failed_chunks),
        'current_index': current_index,
        'total_chunks': len(chunks),
        'timestamp': datetime.now().isoformat(),
        'embedding_provider': embedding_provider
    }

    try:
        with open(CHECKPOINT_FILE, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        logger.info(f"💾 Checkpoint saved - processed: {len(processed_chunks)}, current index: {current_index}")
    except Exception as e:
        logger.error(f"❌ Failed to save checkpoint: {e}")

def load_checkpoint():
    """Load processing progress from checkpoint file"""
    if not os.path.exists(CHECKPOINT_FILE):
        return None

    try:
        with open(CHECKPOINT_FILE, 'rb') as f:
            checkpoint_data = pickle.load(f)

        # Verify checkpoint is for the same provider
        if checkpoint_data.get('embedding_provider') != embedding_provider:
            logger.warning(f"⚠️ Checkpoint is for different provider ({checkpoint_data.get('embedding_provider')}) than current ({embedding_provider})")
            return None

        logger.info(f"📋 Loaded checkpoint - processed: {len(checkpoint_data['processed_chunks'])}, current index: {checkpoint_data['current_index']}")
        return checkpoint_data
    except Exception as e:
        logger.error(f"❌ Failed to load checkpoint: {e}")
        return None

def cleanup_checkpoint():
    """Clean up checkpoint file"""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            logger.info("🗑️ Checkpoint file cleaned up")
    except Exception as e:
        logger.error(f"❌ Failed to cleanup checkpoint: {e}")

def timeout_handler(signum, frame):
    """Handle timeout signals"""
    raise TimeoutError("Processing timed out")

def retry_with_backoff(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY, backoff=2):
    """Retry function with exponential backoff and better error handling"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌ All {max_retries} attempts failed. Final error: {e}")
                raise

            wait_time = delay * (backoff ** attempt)
            logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed: {e}")

            # Special handling for different error types
            if "timeout" in str(e).lower():
                logger.warning(f"⏰ Request timed out. Retrying in {wait_time}s...")
            elif "rate limit" in str(e).lower():
                logger.warning(f"🚦 Rate limited. Retrying in {wait_time}s...")
            elif "server error" in str(e).lower() or "500" in str(e):
                logger.warning(f"🔥 Server error. Retrying in {wait_time}s...")
            else:
                logger.warning(f"❌ Other error. Retrying in {wait_time}s...")

            time.sleep(wait_time)

    raise Exception(f"All {max_retries} attempts failed")

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

# Set up signal handlers for graceful shutdown
if sys.platform != "win32":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

# Initialize database
logger.info("🔧 Initializing database...")
if not initialize_database():
    logger.error("❌ Failed to initialize database")
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

def validate_and_split_chunk(text, max_tokens=MAX_CHUNK_SIZE, emergency_mode=False):
    """Validate chunk size and split if necessary with enhanced splitting logic"""
    from utils.tokenizer import OpenAITokenizerWrapper

    tokenizer = OpenAITokenizerWrapper()
    token_count = len(tokenizer.encode(text))

    logger.info(f"📏 Chunk token count: {token_count} (max: {max_tokens})")

    if token_count <= max_tokens:
        return [text], [token_count]

    # Use emergency chunk size if in emergency mode
    if emergency_mode:
        max_tokens = EMERGENCY_CHUNK_SIZE
        logger.warning(f"🚨 Emergency mode: Using reduced chunk size of {max_tokens} tokens")

    # Enhanced splitting logic for large chunks
    logger.warning(f"⚠️ Chunk too large ({token_count} tokens), splitting into smaller chunks")

    # Try to split by paragraphs first for better semantic boundaries
    paragraphs = text.split('\n\n')
    if len(paragraphs) > 1:
        chunks = []
        current_chunk = []
        current_tokens = 0

        for paragraph in paragraphs:
            para_tokens = len(tokenizer.encode(paragraph))
            
            if para_tokens > max_tokens:
                # Paragraph itself is too large, split by sentences
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence_tokens = len(tokenizer.encode(sentence))
                    
                    if current_tokens + sentence_tokens > max_tokens and current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_tokens = sentence_tokens
                    else:
                        current_chunk.append(sentence)
                        current_tokens += sentence_tokens
            else:
                if current_tokens + para_tokens > max_tokens and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [paragraph]
                    current_tokens = para_tokens
                else:
                    current_chunk.append(paragraph)
                    current_tokens += para_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
    else:
        # Fallback to word-based splitting
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_tokens = len(tokenizer.encode(word + " "))

            if current_tokens + word_tokens > max_tokens and current_chunk:
                # Save current chunk and start new one
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

    # Calculate token counts for all chunks
    token_counts = [len(tokenizer.encode(chunk)) for chunk in chunks]

    logger.info(f"✅ Split into {len(chunks)} chunks with token counts: {token_counts}")

    return chunks, token_counts

def get_embedding(text, emergency_mode=False):
    """Get embedding for text using configured provider with enhanced error handling and emergency mode"""
    # Validate chunk size first with emergency mode if needed
    sub_chunks, token_counts = validate_and_split_chunk(text, emergency_mode=emergency_mode)

    if len(sub_chunks) > 1:
        logger.info(f"🔄 Processing {len(sub_chunks)} sub-chunks for embedding")
        embeddings = []

        for i, sub_chunk in enumerate(sub_chunks):
            logger.info(f"🔄 Getting embedding for sub-chunk {i+1}/{len(sub_chunks)} ({token_counts[i]} tokens)")

            if embedding_provider == "openai":
                try:
                    response = openai_client.embeddings.create(
                        model="text-embedding-3-large",
                        input=sub_chunk,
                        timeout=EMBEDDING_TIMEOUT
                    )
                    embeddings.append(response.data[0].embedding)
                    logger.info(f"✅ Sub-chunk {i+1}/{len(sub_chunks)} embedded successfully")
                except Exception as e:
                    logger.error(f"❌ OpenAI API error for sub-chunk {i+1}: {e}")
                    if "rate limit" in str(e).lower():
                        logger.info("💡 Consider increasing RATE_LIMIT_DELAY to avoid rate limits")
                    elif "timeout" in str(e).lower():
                        logger.info(f"💡 OpenAI request timed out after {EMBEDDING_TIMEOUT}s")
                        if not emergency_mode:
                            logger.info("💡 Will retry with emergency mode (smaller chunks)")
                    raise
            elif embedding_provider == "mistral":
                try:
                    response = mistral_client.embeddings.create(
                        model="mistral-embed",
                        inputs=[sub_chunk]
                    )
                    embeddings.append(response.data[0].embedding)
                    logger.info(f"✅ Sub-chunk {i+1}/{len(sub_chunks)} embedded successfully")
                except Exception as e:
                    logger.error(f"❌ Mistral API error for sub-chunk {i+1}: {e}")
                    if "rate limit" in str(e).lower():
                        logger.info("💡 Consider increasing RATE_LIMIT_DELAY to avoid rate limits")
                    raise

            # Rate limiting delay between sub-chunks
            if i < len(sub_chunks) - 1:
                logger.debug(f"⏳ Rate limiting delay: {RATE_LIMIT_DELAY}s")
                time.sleep(RATE_LIMIT_DELAY)

        # Average the embeddings for the final result
        if embeddings:
            logger.info(f"✅ Generated {len(embeddings)} embeddings, averaging for final result")
            return np.mean(embeddings, axis=0).tolist()

    else:
        # Single chunk processing
        if embedding_provider == "openai":
            try:
                response = openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=text,
                    timeout=EMBEDDING_TIMEOUT
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"❌ OpenAI API error: {e}")
                if "rate limit" in str(e).lower():
                    logger.info("💡 Consider increasing RATE_LIMIT_DELAY to avoid rate limits")
                elif "timeout" in str(e).lower():
                    logger.info(f"💡 OpenAI request timed out after {EMBEDDING_TIMEOUT}s")
                    if not emergency_mode:
                        logger.info("💡 Will retry with emergency mode (smaller chunks)")
                raise
        elif embedding_provider == "mistral":
            try:
                response = mistral_client.embeddings.create(
                    model="mistral-embed",
                    inputs=[text]
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"❌ Mistral API error: {e}")
                if "rate limit" in str(e).lower():
                    logger.info("💡 Consider increasing RATE_LIMIT_DELAY to avoid rate limits")
                raise

def get_embedding_with_emergency_fallback(text):
    """Get embedding with emergency fallback for problematic chunks"""
    try:
        # First attempt with normal mode
        return get_embedding(text, emergency_mode=False)
    except Exception as e:
        if "timeout" in str(e).lower() or "too large" in str(e).lower():
            logger.warning("🚨 First attempt failed, trying emergency mode with smaller chunks...")
            try:
                # Second attempt with emergency mode
                return get_embedding(text, emergency_mode=True)
            except Exception as e2:
                logger.error(f"❌ Emergency mode also failed: {e2}")
                raise e2
        else:
            # Re-raise other types of errors
            raise

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    logger.info("⏹️ Received interrupt signal - shutting down gracefully...")
    logger.info("💡 Progress will be saved. Use --resume to continue later.")
    cleanup_checkpoint()
    sys.exit(0)

# Enhanced embedding processing with timeout handling and resume capability
def process_chunk_with_timeout(chunk_data, chunk_index, total_chunks):
    """Process a single chunk with timeout and retry logic"""
    chunk_id, document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count, document_filename = chunk_data

    def embedding_task():
        """Inner function to generate embedding with timeout"""
        start_time = time.time()

        # Set up timeout signal (signal-based timeout doesn't work well on Windows)
        if sys.platform != "win32":
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(EMBEDDING_TIMEOUT)

        try:
            logger.info(f"🤖 Processing chunk {chunk_index + 1}/{total_chunks} from {document_filename}")
            logger.info(f"📏 Chunk size: {len(chunk_text)} characters, ~{token_count} tokens")

            # Check chunk size before processing
            if token_count > MAX_CHUNK_SIZE:
                logger.warning(f"⚠️ Large chunk detected: {token_count} tokens (max: {MAX_CHUNK_SIZE})")

            embedding = get_embedding_with_emergency_fallback(chunk_text)
            processing_time = time.time() - start_time

            logger.info(f"✅ Generated embedding in {processing_time:.2f}s ({len(embedding)} dimensions)")

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
            logger.info(f"💾 Storing embedding in database for chunk {chunk_id}")

            if store_embedding_in_db(chunk_info, embedding, embedding_provider, model):
                logger.info(f"✅ Successfully processed chunk {chunk_index + 1}/{total_chunks} for {document_filename} ({processing_time:.2f}s)")
                return True
            else:
                logger.error(f"❌ Failed to store embedding {chunk_index + 1}/{total_chunks} for {document_filename}")
                return False

        except TimeoutError:
            processing_time = time.time() - start_time
            logger.error(f"⏰ Timeout after {processing_time:.2f}s for chunk {chunk_index + 1}/{total_chunks}")
            logger.error(f"📄 Document: {document_filename}, Chunk size: ~{token_count} tokens")
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error after {processing_time:.2f}s for chunk {chunk_index + 1}: {e}")
            logger.error(f"📄 Document: {document_filename}, Chunk size: ~{token_count} tokens")
            raise
        finally:
            if sys.platform != "win32":
                signal.alarm(0)  # Cancel the alarm

    # Use retry logic for the embedding task
    return retry_with_backoff(embedding_task, max_retries=MAX_RETRIES, delay=RETRY_DELAY)

# Main processing function with resume capability
def process_embeddings_with_resume(chunks):
    """Process embeddings with resume capability and progress tracking"""
    global processed_chunks, failed_chunks, start_time, last_progress_save

    start_time = time.time()
    successful_stores = 0
    failed_stores = 0

    # Load checkpoint if resume is requested
    checkpoint = None
    resume_index = 0

    if args.resume:
        checkpoint = load_checkpoint()
        if checkpoint:
            processed_chunks = set(checkpoint['processed_chunks'])
            failed_chunks = set(checkpoint['failed_chunks'])
            resume_index = checkpoint['current_index']
            successful_stores = len(processed_chunks)
            failed_stores = len(failed_chunks)
            logger.info(f"📋 Resuming from checkpoint - index {resume_index}, {successful_stores} successful, {failed_stores} failed")

    logger.info(f"🧬 Starting embedding generation using {embedding_provider}")
    logger.info(f"📝 Processing {len(chunks)} chunks with resume capability")

    # Set up overall timeout for the entire process (Windows-compatible)
    overall_start_time = time.time()
    def check_overall_timeout():
        if time.time() - overall_start_time > PROCESSING_TIMEOUT:
            logger.error(f"⏰ Overall process timed out after {PROCESSING_TIMEOUT} seconds")
            raise TimeoutError(f"Process timed out after {PROCESSING_TIMEOUT} seconds")

    if sys.platform != "win32":
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(PROCESSING_TIMEOUT)

    try:
        for i in range(resume_index, len(chunks)):
            chunk_data = chunks[i]

            # Skip if already processed
            if chunk_data[0] in processed_chunks:
                logger.info(f"⏭️ Skipping already processed chunk {i + 1}/{len(chunks)}")
                continue

            # Skip if previously failed (for now - could implement retry logic for failed chunks)
            if chunk_data[0] in failed_chunks:
                logger.warning(f"⏭️ Skipping previously failed chunk {i + 1}/{len(chunks)}")
                failed_stores += 1
                continue

            try:
                # Check overall timeout before processing each chunk
                check_overall_timeout()

                logger.info(f"🔄 Processing chunk {i + 1}/{len(chunks)} from document: {chunk_data[8]} (Chunk ID: {chunk_data[0]})")

                # Process chunk with timeout and retry logic
                if process_chunk_with_timeout(chunk_data, i, len(chunks)):
                    successful_stores += 1
                    processed_chunks.add(chunk_data[0])
                else:
                    failed_stores += 1
                    failed_chunks.add(chunk_data[0])

                # Rate limiting delay
                if i < len(chunks) - 1:  # Don't delay after the last chunk
                    logger.debug(f"⏳ Rate limiting delay: {RATE_LIMIT_DELAY}s")
                    time.sleep(RATE_LIMIT_DELAY)

                # Save progress periodically
                if (i + 1) % PROGRESS_SAVE_INTERVAL == 0:
                    save_checkpoint(chunks, processed_chunks, failed_chunks, i + 1)

                # Log progress
                elapsed_time = time.time() - start_time
                chunks_per_second = (i + 1) / elapsed_time if elapsed_time > 0 else 0
                eta_seconds = (len(chunks) - i - 1) / chunks_per_second if chunks_per_second > 0 else 0

                logger.info(f"📊 Progress: {i + 1}/{len(chunks)} ({((i + 1) / len(chunks)) * 100:.1f}%) - "
                           f"Success: {successful_stores}, Failed: {failed_stores}, "
                           f"Rate: {chunks_per_second:.2f} chunks/s, ETA: {timedelta(seconds=int(eta_seconds))}")

            except Exception as e:
                failed_stores += 1
                failed_chunks.add(chunk_data[0])
                logger.error(f"❌ Error processing chunk {i + 1}: {e}")
                import traceback
                traceback.print_exc()

                # Continue with next chunk instead of stopping
                continue

    except TimeoutError:
        logger.error(f"⏰ Overall process timed out after {PROCESSING_TIMEOUT} seconds")
        logger.info("💡 Process timed out but progress has been saved. Use --resume to continue.")
    except KeyboardInterrupt:
        logger.info("⏹️ Process interrupted by user")
        logger.info("💡 Progress has been saved. Use --resume to continue.")
    finally:
        if sys.platform != "win32":
            signal.alarm(0)  # Cancel the alarm

        # Save final progress
        save_checkpoint(chunks, processed_chunks, failed_chunks, len(chunks))

    return successful_stores, failed_stores

# Process chunks and generate embeddings with robust error handling
successful_stores, failed_stores = process_embeddings_with_resume(chunks)

# Final verification and cleanup
logger.info("🎉 Embedding generation completed!")
logger.info(f"📊 Results: {successful_stores} successful, {failed_stores} failed")

# Calculate processing statistics
if start_time:
    total_time = time.time() - start_time
    chunks_per_second = len(chunks) / total_time if total_time > 0 else 0
    logger.info(f"⏱️ Total processing time: {timedelta(seconds=int(total_time))}")
    logger.info(f"🚀 Average processing rate: {chunks_per_second:.2f} chunks/second")

# Verify embeddings were actually stored
conn = get_db_connection()
if conn:
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM embeddings WHERE embedding_provider = %s", (embedding_provider,))
            total_embeddings = cur.fetchone()[0]
            logger.info(f"📊 Total embeddings in database for {embedding_provider}: {total_embeddings}")

            # Show recent embeddings for verification
            cur.execute("""
                SELECT e.filename, COUNT(*) as embedding_count
                FROM embeddings e
                WHERE e.embedding_provider = %s
                GROUP BY e.filename
                ORDER BY e.created_at DESC
                LIMIT 5
            """, (embedding_provider,))
            recent_files = cur.fetchall()
            if recent_files:
                logger.info("📋 Recent files with embeddings:")
                for filename, count in recent_files:
                    logger.info(f"  • {filename}: {count} embeddings")
    except Exception as e:
        logger.error(f"❌ Error verifying embeddings: {e}")
    finally:
        conn.close()

# Clean up checkpoint file on successful completion
if successful_stores > 0 and failed_stores == 0:
    cleanup_checkpoint()
    logger.info("✅ All embeddings processed successfully - checkpoint cleaned up")
elif successful_stores > 0:
    logger.info("✅ Embeddings successfully stored in Neon database!")
    logger.info(f"💡 Use --resume to continue processing remaining {failed_stores} failed chunks if needed")
    logger.info("💡 Checkpoint file preserved for potential resume")
else:
    logger.error("❌ No embeddings were successfully stored")
    logger.info("💡 Check the error messages above for troubleshooting information")
    logger.info("💡 Use --resume to retry failed chunks")

# Show helpful next steps
if successful_stores > 0:
    logger.info("🚀 Next steps:")
    logger.info("  1. Use the chat interface (5-chat.py) to ask questions about your documents")
    logger.info("  2. Run this script again with --resume if there were failures")
    logger.info("  3. Check embedding_process.log for detailed processing information")

    # Show configuration tips for large files
    logger.info("📋 Configuration for large files:")
    logger.info(f"  • EMBEDDING_TIMEOUT: {EMBEDDING_TIMEOUT}s per chunk")
    logger.info(f"  • MAX_RETRIES: {MAX_RETRIES} attempts per chunk")
    logger.info(f"  • RATE_LIMIT_DELAY: {RATE_LIMIT_DELAY}s between requests")
    logger.info(f"  • PROCESSING_TIMEOUT: {PROCESSING_TIMEOUT}s overall limit")
    logger.info("  • Use --resume to continue interrupted processing")