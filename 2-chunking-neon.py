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

# Set up Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Suppress the specific transformers warning
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*", category=FutureWarning)

# Neon database connection
NEON_CONNECTION_STRING = "postgresql://neondb_owner:npg_N7vynH6dQCer@ep-gentle-moon-aeeiaefq-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

def get_db_connection():
    """Get connection to Neon database"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_unprocessed_documents():
    """Get all unprocessed documents from the database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, filename, file_path, file_type, content
                FROM documents 
                WHERE processed = FALSE
                ORDER BY upload_date DESC
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
            return documents
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []
    finally:
        conn.close()

def insert_chunk_into_db(document_id, chunk_text, chunk_index, page_numbers=None, section_title=None, chunk_type="text", token_count=None):
    """Insert a chunk into the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO document_chunks (document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error inserting chunk: {e}")
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
    tokenizer = OpenAITokenizerWrapper()
    MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length
    
    # Initialize DocumentConverter
    converter = DocumentConverter()
    
    # Get unprocessed documents from database
    documents = get_unprocessed_documents()
    
    if not documents:
        print("✅ No unprocessed documents found in database")
        return
    
    print(f"Found {len(documents)} unprocessed document(s) in database")
    
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
            for i, chunk in enumerate(chunks):
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