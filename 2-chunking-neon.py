from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from docling.datamodel.document import DoclingDocument, TextItem
from dotenv import load_dotenv
from utils.tokenizer import OpenAITokenizerWrapper
import psycopg2
import os
import sys
import warnings
import tempfile

load_dotenv()

# Neon database connection - loaded from environment variables
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

# Validate required environment variables
if not NEON_CONNECTION_STRING:
    print("NEON_CONNECTION_STRING environment variable is required but not set!")
    exit(1)

# Set up Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Suppress the specific transformers warning
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning)

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

def get_unprocessed_documents():
    """Get all unprocessed documents from the database"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            # Check if document_chunks table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'document_chunks'
                )
            """)
            chunks_table_exists = cur.fetchone()[0]

            if not chunks_table_exists:
                print("❌ document_chunks table does not exist - creating it...")
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
                conn.commit()
                print("✅ Created document_chunks table")

            # Get documents that exist but don't have chunks yet
            cur.execute("""
                SELECT d.id, d.filename, d.file_path, d.file_type, d.content
                FROM documents d
                LEFT JOIN document_chunks dc ON d.id = dc.document_id
                WHERE dc.document_id IS NULL
                ORDER BY d.upload_date DESC
            """)
            documents = []
            for row in cur.fetchall():
                doc = {
                    "id": row[0],
                    "filename": row[1],
                    "file_path": row[2],
                    "file_type": row[3],
                    "content": row[4]
                }
                documents.append(doc)

            print(f"📊 Found {len(documents)} documents without chunks")
            return documents
    except Exception as e:
        print(f"❌ Error fetching documents: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()

def insert_chunk_into_db(document_id, chunk_text, chunk_index, page_numbers=None, section_title=None, chunk_type="text", token_count=None):
    """Insert a chunk into the database"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database for chunk insertion")
        return False

    try:
        with conn.cursor() as cur:
            # First verify the document exists
            cur.execute("SELECT filename FROM documents WHERE id = %s", (document_id,))
            doc_result = cur.fetchone()
            if not doc_result:
                print(f"❌ Document with ID {document_id} not found")
                return False

            doc_filename = doc_result[0]
            print(f"💾 Inserting chunk {chunk_index} for document: {doc_filename}")

            cur.execute("""
                INSERT INTO document_chunks (document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count))

            chunk_id = cur.fetchone()[0]
            conn.commit()
            print(f"✅ Chunk {chunk_index} inserted successfully (ID: {chunk_id})")
            return True
    except Exception as e:
        print(f"❌ Error inserting chunk {chunk_index}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def mark_document_processed(document_id):
    """Mark a document as processed in the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE documents 
                SET processed = TRUE, processing_date = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (document_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error marking document as processed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def process_text_file_with_docling(file_path):
    """Process text files by treating them as markdown files"""
    from docling.datamodel.base_models import InputFormat
    
    # Create a temporary file with .md extension
    import tempfile
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    # Use DocumentConverter to process the temporary markdown file
    converter = DocumentConverter(allowed_formats=[InputFormat.MD])
    result = converter.convert(temp_file_path)
    
    # Clean up temporary file
    os.unlink(temp_file_path)
    
    return result

def process_document_chunking():
    """Main function to process document chunking from database"""
    print("🔧 Initializing database...")
    if not initialize_database():
        print("❌ Failed to initialize database")
        return

    tokenizer = OpenAITokenizerWrapper()
    MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

    # Initialize DocumentConverter
    converter = DocumentConverter()

    # Get documents that need chunking
    documents = get_unprocessed_documents()

    if not documents:
        print("✅ No documents found that need chunking")

        # Check if there are any documents at all
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM documents")
                    total_docs = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM document_chunks")
                    total_chunks = cur.fetchone()[0]
                    print(f"📊 Database status: {total_docs} documents, {total_chunks} chunks")
            finally:
                conn.close()

        return

    print(f"🔍 Found {len(documents)} document(s) that need chunking")
    
    total_chunks_created = 0
    
    for doc in documents:
        print(f"\nProcessing document: {doc['filename']} (ID: {doc['id']})")
        
        try:
            # For text files that already have content in the database
            if doc['content'] and doc['file_type'] in ['txt', 'md', 'html']:
                # Handle .txt files specially by converting them to markdown format
                if doc['file_type'] == 'txt':
                    if os.path.exists(doc['file_path']):
                        result = process_text_file_with_docling(doc['file_path'])
                    else:
                        print(f"❌ File not found: {doc['file_path']}")
                        continue
                else:
                    # For markdown and HTML files, use the original file path
                    if os.path.exists(doc['file_path']):
                        result = converter.convert(doc['file_path'])
                    else:
                        print(f"❌ File not found: {doc['file_path']}")
                        continue
                
            else:
                # For binary files (PDF, DOCX, etc.), use the original file path
                if os.path.exists(doc['file_path']):
                    result = converter.convert(doc['file_path'])
                else:
                    print(f"❌ File not found: {doc['file_path']}")
                    continue
            
            # Apply hybrid chunking
            chunker = HybridChunker(
                tokenizer=tokenizer,
                max_tokens=MAX_TOKENS,
                merge_peers=True,
            )
            
            chunk_iter = chunker.chunk(dl_doc=result.document)
            chunks = list(chunk_iter)
            
            print(f"Created {len(chunks)} chunks for {doc['filename']}")
            
            # Insert chunks into database
            chunks_inserted = 0
            print(f"💾 Inserting {len(chunks)} chunks into database...")

            for i, chunk in enumerate(chunks):
                try:
                    # Extract chunk metadata
                    page_numbers = None
                    section_title = None
                    chunk_type = "text"

                    # Try to extract metadata from chunk
                    if hasattr(chunk, 'metadata'):
                        if 'page_numbers' in chunk.metadata:
                            page_numbers = chunk.metadata['page_numbers']
                        if 'section_title' in chunk.metadata:
                            section_title = chunk.metadata['section_title']
                        if 'chunk_type' in chunk.metadata:
                            chunk_type = chunk.metadata['chunk_type']

                    # Calculate token count
                    token_count = len(tokenizer.encode(chunk.text))

                    # Insert chunk into database
                    if insert_chunk_into_db(
                        document_id=doc['id'],
                        chunk_text=chunk.text,
                        chunk_index=i,
                        page_numbers=page_numbers,
                        section_title=section_title,
                        chunk_type=chunk_type,
                        token_count=token_count
                    ):
                        chunks_inserted += 1
                        if (i + 1) % 5 == 0:  # Progress update every 5 chunks
                            print(f"  📝 Inserted {i + 1}/{len(chunks)} chunks...")
                    else:
                        print(f"❌ Failed to insert chunk {i}")
                except Exception as e:
                    print(f"❌ Error processing chunk {i}: {e}")
            
            if chunks_inserted > 0:
                # Mark document as processed
                if mark_document_processed(doc['id']):
                    print(f"✅ Successfully processed {doc['filename']} - inserted {chunks_inserted} chunks")
                    total_chunks_created += chunks_inserted
                else:
                    print(f"❌ Failed to mark document as processed: {doc['filename']}")
            else:
                print(f"❌ No chunks inserted for: {doc['filename']}")
                
        except Exception as e:
            print(f"❌ Error processing {doc['filename']}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Chunking completed! Total chunks created: {total_chunks_created}")
    
    # Verify the results
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM document_chunks")
                total_chunks = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM documents WHERE processed = TRUE")
                processed_docs = cur.fetchone()[0]
                print(f"📊 Database summary: {total_chunks} total chunks, {processed_docs} processed documents")
        except Exception as e:
            print(f"Error verifying results: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    print("Starting database-based chunking process...")
    process_document_chunking()
    print("Chunking process completed!")