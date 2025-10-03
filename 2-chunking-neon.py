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
import time
from typing import List, Tuple, Optional
import logging
import re

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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration constants for better semantic preservation
DOCUMENT_PROCESSING_TIMEOUT = 600  # 10 minutes timeout per document
CHUNK_INSERTION_BATCH_SIZE = 10    # Insert chunks in batches of 10
PROGRESS_UPDATE_INTERVAL = 5       # Update progress every 5 chunks
MAX_TOKENS = 8191                  # text-embedding-3-large's maximum context length

# Enhanced chunking parameters for better semantic coherence
OPTIMAL_CHUNK_SIZE = 2048          # Optimal chunk size for semantic meaning
MIN_CHUNK_SIZE = 512               # Minimum chunk size to maintain context
SEMANTIC_OVERLAP = 256             # Overlap between chunks for better coherence

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

            # Get documents that have content (reprocess all for metadata enhancement)
            cur.execute("""
                SELECT d.id, d.filename, d.file_path, d.file_type, d.content
                FROM documents d
                WHERE d.content IS NOT NULL
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

            print(f"📊 Found {len(documents)} documents with content but without chunks")
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

def insert_chunks_batch(document_id: int, chunks_data: List[Tuple]) -> bool:
    """Insert multiple chunks into the database in a single batch"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database for batch chunk insertion")
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
            print(f"💾 Inserting {len(chunks_data)} chunks for document: {doc_filename}")

            # Format chunks data - fix page_numbers array format
            formatted_chunks_data = []
            for chunk_data in chunks_data:
                # chunk_data is (document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count)
                page_numbers = chunk_data[3]  # index 3 is page_numbers

                # Format page_numbers as proper PostgreSQL array or NULL
                if page_numbers:
                    # Convert string like "1,2,3" to PostgreSQL array format "{1,2,3}"
                    if isinstance(page_numbers, str):
                        # Remove any existing braces and split by comma
                        clean_pages = page_numbers.strip('{}').split(',')
                        # Filter out empty strings and convert to integers
                        page_list = [p.strip() for p in clean_pages if p.strip()]
                        if page_list:
                            page_numbers_formatted = '{' + ','.join(page_list) + '}'
                        else:
                            page_numbers_formatted = None
                    else:
                        page_numbers_formatted = None
                else:
                    page_numbers_formatted = None

                # Create new tuple with formatted page_numbers
                formatted_chunk_data = (
                    chunk_data[0],  # document_id
                    chunk_data[1],  # chunk_text
                    chunk_data[2],  # chunk_index
                    page_numbers_formatted,  # formatted page_numbers
                    chunk_data[4],  # section_title
                    chunk_data[5],  # chunk_type
                    chunk_data[6]   # token_count
                )
                formatted_chunks_data.append(formatted_chunk_data)

            # Prepare batch insert
            insert_query = """
                INSERT INTO document_chunks (document_id, chunk_text, chunk_index, page_numbers, section_title, chunk_type, token_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cur.executemany(insert_query, formatted_chunks_data)
            conn.commit()
            print(f"✅ Successfully inserted {len(chunks_data)} chunks")
            return True
    except Exception as e:
        print(f"❌ Error in batch chunk insertion: {e}")
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

def extract_page_numbers_from_text(text: str) -> str:
    """Extract page numbers from chunk text content with enhanced detection"""
    if not text:
        return None

    # Look for metadata comments first (enhanced patterns)
    metadata_patterns = [
        r'<!--\s*PAGE:\s*([^>]+?)\s*-->',  # <!-- PAGE: 23 -->
        r'<!--\s*PAGE:\s*(\d+)',           # <!-- PAGE: 23
        r'<!--.*?page.*?(\d+).*?-->',      # <!-- ... page 23 ... -->
        r'page\s*:\s*(\d+)',               # page: 23
        r'pages?\s*:\s*(\d+)',             # page: 23 or pages: 23
    ]

    for pattern in metadata_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            page_info = match.group(1).strip()
            # Extract just the numbers
            numbers = re.findall(r'\d+', page_info)
            if numbers:
                return ",".join(numbers)

    # Look for explicit page number patterns in various formats (including French)
    page_patterns = [
        r'page\s+(\d+)',                   # "page 23"
        r'Page\s+(\d+)',                   # "Page 23"
        r'p\.\s*(\d+)',                    # "p. 23"
        r'pp\.\s*(\d+)',                   # "pp. 23"
        r'pg\.\s*(\d+)',                   # "pg. 23"
        r'^\s*(\d+)\s*$',                  # Just a number on its own line
        r'\(page\s+(\d+)\)',               # (page 23)
        r'\[page\s+(\d+)\]',               # [page 23]
        r'-\s*(\d+)\s*-',                  # - 23 -
        r'\|.*?(\d+).*?\|',                # | ... 23 ... |
    ]

    found_pages = []
    for pattern in page_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if match.isdigit():
                page_num = int(match)
                # Filter out unreasonable page numbers (too high or too low)
                if 1 <= page_num <= 10000:  # Reasonable page range
                    found_pages.append(page_num)

    if found_pages:
        # Return unique page numbers, sorted
        unique_pages = sorted(set(found_pages))
        if len(unique_pages) == 1:
            return str(unique_pages[0])
        else:
            return ",".join(str(p) for p in unique_pages)

    # Try to infer page numbers from document structure
    # Look for patterns that might indicate page breaks or sections
    lines = text.strip().split('\n')
    page_indicators = []

    for line in lines[:15]:  # Check first 15 lines for better coverage
        line = line.strip()
        # Look for lines that might contain page information
        if (len(line) < 100 and  # Short to medium lines
            any(keyword in line.lower() for keyword in ['page', 'p.', 'pg.', 'partie', 'section']) and
            any(char.isdigit() for char in line)):
            numbers = re.findall(r'\d+', line)
            for num in numbers:
                if 1 <= int(num) <= 10000:
                    page_indicators.append(int(num))

    if page_indicators:
        unique_pages = sorted(set(page_indicators))
        if len(unique_pages) == 1:
            return str(unique_pages[0])
        else:
            return ",".join(str(p) for p in unique_pages)

    return None

def extract_section_title_from_text(text: str) -> str:
    """Extract section title from chunk text content with enhanced detection for French documents"""
    if not text:
        return None

    # Look for metadata comments first (enhanced patterns)
    metadata_patterns = [
        r'<!--\s*SECTION:\s*([^>]+?)\s*-->',  # <!-- SECTION: Planification hebdomadaire -->
        r'<!--.*?section.*?([^>]+?)\s*-->',   # <!-- ... section Planification hebdomadaire ... -->
        r'<!--.*?title.*?([^>]+?)\s*-->',     # <!-- ... title Planification hebdomadaire ... -->
        r'section\s*:\s*([^<\n]+)',           # section: Planification hebdomadaire
        r'title\s*:\s*([^<\n]+)',             # title: Planification hebdomadaire
    ]

    for pattern in metadata_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            # Clean up the title (remove excessive whitespace and special chars)
            title = re.sub(r'\s+', ' ', title)
            title = re.sub(r'[^\w\s\-.,()&]', '', title)  # Keep only safe characters
            if title and len(title) > 3:  # Must be meaningful length
                return title[:200]

    lines = text.strip().split('\n')

    # Look for section headers with enhanced patterns (including French)
    section_patterns = [
        r'^\s*(\d+\.\d+\.?\s+.+?)\s*$',                    # "3.3. Planification hebdomadaire"
        r'^\s*(\d+\.\s+.+?)\s*$',                           # "3. Planification hebdomadaire"
        r'^\s*(Chapter\s+\d+\.?\s+.+?)\s*$',               # "Chapter 3. Something"
        r'^\s*(Section\s+\d+\.?\s+.+?)\s*$',               # "Section 3. Something"
        r'^\s*(Part\s+\d+\.?\s+.+?)\s*$',                  # "Part 3. Something"
        r'^\s*(Article\s+\d+\.?\s+.+?)\s*$',               # "Article 3. Something"
        r'^\s*([A-Z]\.\s+.+?)\s*$',                        # "A. Something"
        r'^\s*([IVX]+\.\s+.+?)\s*$',                       # "I. Something" (Roman numerals)
        r'^\s*(\d+\)\s+.+?)\s*$',                          # "1) Something"
        r'^\s*([A-Z][^.!?]*[A-Z])\s*$',                    # "ALL CAPS TITLES"
        r'^\s*PARTIE\s+(\d+)',                             # "PARTIE 1"
        r'^\s*#\s+(.+?)\s*$',                              # "# Title"
        r'^\s*##\s+(.+?)\s*$',                             # "## Title"
    ]

    for line in lines[:12]:  # Check first 12 lines for better coverage
        line = line.strip()
        if not line or len(line) < 3:  # Skip very short lines
            continue

        for pattern in section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up the title
                title = re.sub(r'\s+', ' ', title)
                title = re.sub(r'[^\w\s\-.,()&àâäéèêëïîôùûüÿç]', '', title)  # Keep French characters

                # Filter out titles that are too short or look like false positives
                if (len(title) > 3 and len(title) < 300 and
                    not title.isdigit() and
                    title.lower() not in ['table of contents', 'contents', 'index', 'summary', 'table des matières', 'sommaire'] and
                    not all(word in title.lower() for word in ['random', 'text', 'without', 'structure', 'test'])):  # Avoid test data
                    return title[:200]

    # Look for meaningful first lines that could be titles (including French patterns)
    for line in lines[:8]:
        line = line.strip()
        if (len(line) > 8 and len(line) < 200 and
            not line.isdigit() and
            not line.startswith('•') and  # Avoid bullet points
            not line.startswith('-') and  # Avoid dashes
            not line.startswith('*') and  # Avoid asterisks
            not line.startswith('>') and  # Avoid quotes
            not any(keyword in line.lower() for keyword in ['http', 'www.', '@', '![', 'img-'])):  # Avoid URLs/emails/images

            # Check if line starts with capital letter or number followed by period (French style)
            if (line[0].isupper() or
                (len(line) > 3 and line[0].isdigit() and line[1:3] in ['. ', ' -']) or
                line.upper() == line):  # ALL CAPS titles

                # Clean up the title
                title = re.sub(r'\s+', ' ', line)
                title = re.sub(r'[^\w\s\-.,()&àâäéèêëïîôùûüÿç]', '', title)

                if len(title) > 5:
                    return title[:200]

    # Look for bold or emphasized text that might be titles
    bold_patterns = [
        r'\*\*(.*?)\*\*',        # **Bold text**
        r'__(.*?)__',            # __Bold text__
        r'\*(.*?)\*',            # *Italic text*
        r'`(.*?)`',              # `Code text`
    ]

    for pattern in bold_patterns:
        matches = re.findall(pattern, text[:800])  # Check first 800 chars
        for match in matches:
            if (len(match) > 5 and len(match) < 150 and
                (match[0].isupper() or match[0].isdigit()) and
                (not any(char.isdigit() for char in match[:2]) or match[0].isdigit())):
                clean_title = re.sub(r'[^\w\s\-.,()&àâäéèêëïîôùûüÿç]', '', match)
                if len(clean_title) > 5:
                    return clean_title[:200]

    return None


def process_document_with_timeout(process_func, timeout_seconds, *args, **kwargs):
    """Execute a function with a timeout using threading"""
    import threading
    import queue

    def target_func(result_queue, *args, **kwargs):
        try:
            result = process_func(*args, **kwargs)
            result_queue.put(('success', result))
        except Exception as e:
            result_queue.put(('error', e))

    # Create a queue to get the result
    result_queue = queue.Queue()

    # Start the function in a separate thread
    thread = threading.Thread(
        target=target_func,
        args=(result_queue,) + args,
        kwargs=kwargs
    )
    thread.daemon = True
    thread.start()

    # Wait for completion or timeout
    thread.join(timeout_seconds)

    if thread.is_alive():
        print(f"⏰ Document processing timed out after {timeout_seconds} seconds")
        return None
    else:
        try:
            status, result = result_queue.get_nowait()
            if status == 'success':
                return result
            else:
                print(f"❌ Error in document processing: {result}")
                return 0
        except queue.Empty:
            print("❌ Unexpected error: no result from processing thread")
            return 0

def process_single_document(doc, tokenizer, converter, chunker):
    """Process a single document with optimized chunking from database content"""
    print(f"\n📄 Processing document: {doc['filename']} (ID: {doc['id']})")
    start_time = time.time()

    # Delete existing chunks for this document to avoid duplicates
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM document_chunks WHERE document_id = %s", (doc['id'],))
                deleted_count = cur.rowcount
                if deleted_count > 0:
                    print(f"🗑️ Deleted {deleted_count} existing chunks for reprocessing")
                conn.commit()
        except Exception as e:
            print(f"⚠️ Warning: Could not delete existing chunks: {e}")
        finally:
            conn.close()

    try:
        # Check if document has content in database
        if not doc['content'] or doc['content'].strip() == '':
            print(f"❌ No content found in database for document: {doc['filename']}")
            print(f"   Document ID: {doc['id']}")
            print(f"   Content length: {len(doc['content']) if doc['content'] else 0}")
            print("   This document needs to be extracted first using the '🚀 Extract' button")
            return 0

        print(f"📝 Document has {len(doc['content'])} characters of extracted content")

        # Create a temporary markdown file from the database content
        import tempfile
        import uuid

        # Create temporary file with proper extension based on content
        temp_filename = f"temp_{uuid.uuid4()}.md"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(doc['content'])
            temp_file_path = temp_file.name

        try:
            # Use DocumentConverter to process the temporary markdown file
            print("🔄 Converting extracted content to DoclingDocument...")
            from docling.datamodel.base_models import InputFormat
            converter_temp = DocumentConverter(allowed_formats=[InputFormat.MD])
            result = converter_temp.convert(temp_file_path)

            # Apply hybrid chunking with optimized parameters
            print("🔄 Applying hybrid chunking with semantic optimization...")
            chunk_iter = chunker.chunk(dl_doc=result.document)
            chunks = list(chunk_iter)

            print(f"✅ Created {len(chunks)} chunks for {doc['filename']}")

            if len(chunks) == 0:
                print("⚠️ Warning: No chunks were created. This might indicate an issue with the content format.")
                return 0

            # Process chunks in batches
            chunks_inserted = 0
            print(f"💾 Inserting {len(chunks)} chunks into database...")

            # Prepare chunks data for batch insertion
            chunks_data = []
            for i, chunk in enumerate(chunks):
                # Extract chunk metadata with enhanced detection
                page_numbers = None
                section_title = None
                chunk_type = "text"

                # First try to get metadata from the chunk object itself
                if hasattr(chunk, 'meta') and chunk.meta:
                    meta = chunk.meta

                    # Try different ways to access page numbers from Docling
                    if hasattr(meta, 'page_numbers') and meta.page_numbers:
                        page_numbers = str(meta.page_numbers)
                    elif hasattr(meta, 'pages') and meta.pages:
                        page_numbers = str(meta.pages)
                    elif hasattr(meta, 'page') and meta.page:
                        page_numbers = str(meta.page)

                    # Try different ways to access section titles
                    if hasattr(meta, 'section_title') and meta.section_title:
                        section_title = str(meta.section_title)
                    elif hasattr(meta, 'title') and meta.title:
                        section_title = str(meta.title)
                    elif hasattr(meta, 'heading') and meta.heading:
                        section_title = str(meta.heading)

                    # Get chunk type
                    if hasattr(meta, 'chunk_type'):
                        chunk_type = str(meta.chunk_type)
                    elif hasattr(meta, 'type'):
                        chunk_type = str(meta.type)

                # Enhanced page number extraction from text content (fallback)
                if not page_numbers:
                    page_numbers = extract_page_numbers_from_text(chunk.text)

                # Enhanced section title extraction from text content (fallback)
                if not section_title:
                    section_title = extract_section_title_from_text(chunk.text)

                # Additional metadata extraction from chunk structure
                if hasattr(chunk, 'text') and chunk.text:
                    # Look for document structure indicators in the text
                    text_content = chunk.text

                    # Try to infer page numbers from document position if not found
                    if not page_numbers and i > 0:
                        # Estimate page number based on chunk position (rough heuristic)
                        estimated_page = max(1, (i * 2) + 1)  # Assume ~2 chunks per page
                        if estimated_page <= 100:  # Only for reasonable page counts
                            page_numbers = str(estimated_page)

                    # Look for table/figure captions that might indicate sections
                    if not section_title:
                        caption_patterns = [
                            r'(?:Table|Figure|Fig\.|Tableau|Figure|Fig\.)\s+\d+\.?\s*:?\s*(.+?)(?:\n|$)',
                            r'(?:Chart|Graph|Diagram|Graphique|Diagramme)\s+\d+\.?\s*:?\s*(.+?)(?:\n|$)',
                        ]
                        for pattern in caption_patterns:
                            match = re.search(pattern, text_content, re.IGNORECASE)
                            if match:
                                caption_title = match.group(1).strip()
                                if len(caption_title) > 5 and len(caption_title) < 100:
                                    section_title = caption_title
                                    break

                    # Enhanced fallback: Look for document structure patterns
                    if not section_title:
                        # Look for French document patterns
                        french_patterns = [
                            r'^\s*PARTIE\s+(\d+)',  # "PARTIE 1"
                            r'^\s*(\d+\.\s+[A-ZÉÈÊÀÂÔÛÇ].*?)\s*$',  # "1. GÉNÉRALITÉS"
                            r'^\s*([A-ZÉÈÊÀÂÔÛÇ][^.!?]*?)\s*$',  # "TITLES IN CAPS"
                        ]

                        for pattern in french_patterns:
                            match = re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                            if match:
                                potential_title = match.group(1).strip() if match.groups() else match.group(0).strip()
                                if len(potential_title) > 5 and len(potential_title) < 150:
                                    section_title = potential_title
                                    break

                    # Final fallback: Use first meaningful line as section title
                    if not section_title:
                        lines = text_content.strip().split('\n')
                        for line in lines[:3]:  # Check first 3 lines
                            line = line.strip()
                            if (len(line) > 10 and len(line) < 100 and
                                line[0].isupper() and
                                not line.isdigit() and
                                not any(keyword in line.lower() for keyword in ['http', 'www.', '![', 'img-'])):
                                section_title = line[:100]
                                break

                # Calculate token count
                token_count = len(tokenizer.encode(chunk.text))

                # Debug: Print metadata extraction results for first few chunks
                if i < 5:  # Show more chunks for debugging
                    print(f"  Chunk {i}: pages='{page_numbers}', title='{section_title}', type='{chunk_type}'")
                    print(f"    Text preview: {chunk.text[:100]}...")

                # Prepare data for batch insertion
                chunk_data = (
                    doc['id'],
                    chunk.text,
                    i,
                    page_numbers,
                    section_title,
                    chunk_type,
                    token_count
                )
                chunks_data.append(chunk_data)

                # Insert in batches
                if len(chunks_data) >= CHUNK_INSERTION_BATCH_SIZE:
                    if insert_chunks_batch(doc['id'], chunks_data):
                        chunks_inserted += len(chunks_data)
                        print(f"  📝 Inserted {chunks_inserted}/{len(chunks)} chunks...")
                    else:
                        print(f"❌ Failed to insert batch of {len(chunks_data)} chunks")
                        return chunks_inserted
                    chunks_data = []

                # Progress update
                if (i + 1) % PROGRESS_UPDATE_INTERVAL == 0:
                    progress = ((i + 1) / len(chunks)) * 100
                    print(f"  📊 Progress: {progress:.1f}% ({i + 1}/{len(chunks)} chunks)")

            # Insert remaining chunks
            if chunks_data:
                if insert_chunks_batch(doc['id'], chunks_data):
                    chunks_inserted += len(chunks_data)
                else:
                    print(f"❌ Failed to insert final batch of {len(chunks_data)} chunks")
                    return chunks_inserted

            processing_time = time.time() - start_time
            print(f"✅ Successfully processed {doc['filename']} - inserted {chunks_inserted} chunks in {processing_time:.2f} seconds")

            # Show some metadata statistics
            chunks_with_pages = len([c for c in chunks_data if c[3]])  # page_numbers is at index 3
            chunks_with_titles = len([c for c in chunks_data if c[4]])  # section_title is at index 4
            print(f"📊 Metadata extraction: {chunks_with_pages} chunks with page numbers, {chunks_with_titles} chunks with section titles")

            return chunks_inserted

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                print("🗑️ Cleaned up temporary file")
            except Exception as e:
                print(f"⚠️ Warning: Could not delete temporary file {temp_file_path}: {e}")

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Error processing {doc['filename']} after {processing_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
        return 0

def process_document_chunking():
    """Main function to process document chunking from database with optimizations"""
    print("🔧 Initializing database...")
    if not initialize_database():
        print("❌ Failed to initialize database")
        return

    tokenizer = OpenAITokenizerWrapper()

    # Initialize DocumentConverter with optimized settings
    print("🔧 Initializing DocumentConverter...")
    converter = DocumentConverter()

    # Initialize optimized chunker with better semantic preservation
    print("🔧 Initializing HybridChunker with semantic optimization...")
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=MAX_TOKENS,
        merge_peers=True,
        # Enhanced parameters for better semantic coherence
        similarity_threshold=0.85,  # Higher threshold for better chunk cohesion
        merge_strategy="semantic",  # Use semantic merging instead of just token-based
    )

    # Get documents that need chunking
    print("🔍 Fetching documents with content that need chunking...")
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
                    cur.execute("SELECT COUNT(*) FROM documents WHERE content IS NOT NULL")
                    docs_with_content = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM document_chunks")
                    total_chunks = cur.fetchone()[0]
                    print(f"📊 Database status: {total_docs} total documents, {docs_with_content} with content, {total_chunks} chunks")

                    if docs_with_content == 0:
                        print("⚠️ No documents have extracted content. Please run extraction first using the '🚀 Extract' button.")
                    else:
                        print("✅ All documents with content have been chunked.")
            finally:
                conn.close()

        return

    print(f"🔍 Found {len(documents)} document(s) with content that need chunking")

    if len(documents) == 0:
        print("ℹ️ No documents need chunking. All documents with content have already been processed.")
        return

    total_chunks_created = 0

    for doc in documents:
        print(f"\n{'='*60}")
        print(f"📄 Processing document: {doc['filename']} (ID: {doc['id']})")
        print(f"{'='*60}")

        # Process document with timeout
        chunks_created = process_document_with_timeout(
            process_single_document,
            DOCUMENT_PROCESSING_TIMEOUT,
            doc,
            tokenizer,
            converter,
            chunker
        )

        if chunks_created is None:
            print(f"⏰ Document {doc['filename']} timed out - skipping")
            continue
        elif chunks_created > 0:
            total_chunks_created += chunks_created
            # Mark document as processed
            if mark_document_processed(doc['id']):
                print(f"✅ Document {doc['filename']} marked as processed")
            else:
                print(f"❌ Failed to mark document {doc['filename']} as processed")
        else:
            print(f"❌ No chunks were created for document {doc['filename']}")
            print("   This might indicate the document content is empty or in an unsupported format")
    
    print(f"\n{'='*60}")
    print(f"🎉 Chunking completed! Total chunks created: {total_chunks_created}")
    print(f"{'='*60}")

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
            print(f"❌ Error verifying results: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting optimized database-based chunking process...")
    process_document_chunking()
    print("✅ Chunking process completed!")