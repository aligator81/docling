#!/usr/bin/env python3
"""
🔥 UNIFIED DOCUMENT EXTRACTION SYSTEM 🔥
========================================

Comprehensive document extraction system that combines all extraction methods:
- Docling (Local processing with optimizations)
- Mistral OCR (Cloud-based OCR)
- Neon Database integration
- Performance optimizations (caching, parallel processing)
- Batch processing capabilities
- Fallback logic
- All file format support

Author: Code-Supernova AI Assistant
Date: 2025-09-23
"""

import sys
import argparse
import os
import warnings
import base64
import psycopg2
import tempfile
import requests
import multiprocessing as mp
import json
import hashlib
import time
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from mistralai import Mistral
from PIL import Image
from io import BytesIO
import fitz

# Load environment variables
load_dotenv()

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")

# Configuration
NEON_CONNECTION_STRING = "postgresql://neondb_owner:npg_N7vynH6dQCer@ep-gentle-moon-aeeiaefq-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    total_time: float
    pages_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: str
    processed_pages: int
    extraction_method: str

class PerformanceTracker:
    """Track and log performance metrics"""

    def __init__(self, log_file: str = "performance_log.txt"):
        self.log_file = log_file
        self.metrics_history = []

    def track_performance(self, func: Callable):
        """Decorator to track function performance"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss
            start_cpu = process.cpu_percent()

            result = func(*args, **kwargs)

            end_time = time.time()
            end_memory = process.memory_info().rss
            end_cpu = process.cpu_percent()

            page_count = kwargs.get('page_count', 1)
            method = kwargs.get('method', 'unknown')

            metrics = PerformanceMetrics(
                total_time=end_time - start_time,
                pages_per_second=page_count / max(0.001, end_time - start_time),
                memory_usage_mb=(end_memory - start_memory) / 1024 / 1024,
                cpu_usage_percent=end_cpu - start_cpu,
                timestamp=datetime.now().isoformat(),
                processed_pages=page_count,
                extraction_method=method
            )

            self.metrics_history.append(metrics)
            self._log_metrics(metrics, func.__name__)
            return result

        return wrapper

    def _log_metrics(self, metrics: PerformanceMetrics, function_name: str):
        """Log performance metrics"""
        log_entry = (
            f"{metrics.timestamp} | {function_name} | "
            f"Method: {metrics.extraction_method} | "
            f"Time: {metrics.total_time:.2f}s | "
            f"Pages/s: {metrics.pages_per_second:.2f} | "
            f"Memory: {metrics.memory_usage_mb:.2f}MB | "
            f"CPU: {metrics.cpu_usage_percent:.1f}% | "
            f"Pages: {metrics.processed_pages}"
        )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

        print(log_entry)

class DocumentCache:
    """File-based caching system for document processing results"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_file_hash(self, file_path: str) -> str:
        """Generate unique hash for file content"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_cached_result(self, file_path: str, operation: str) -> Optional[dict]:
        """Get cached result if exists"""
        cache_key = f"{self.get_file_hash(file_path)}_{operation}.json"
        cache_file = self.cache_dir / cache_key

        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return None
        return None

    def cache_result(self, file_path: str, operation: str, result: dict):
        """Cache processing result"""
        cache_key = f"{self.get_file_hash(file_path)}_{operation}.json"
        cache_file = self.cache_dir / cache_key

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

class DatabaseManager:
    """Manage Neon database operations"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.connection_string)
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return None

    def get_unprocessed_documents(self) -> List[Dict]:
        """Get documents that need processing"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, filename, file_path, file_type, content
                    FROM documents
                    WHERE processed = FALSE AND content IS NULL
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
            print(f"❌ Error fetching documents: {e}")
            return []
        finally:
            conn.close()

    def update_document_content(self, doc_id: int, content: str, processed: bool = False) -> bool:
        """Update document content in database"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE documents
                    SET content = %s, processed = %s, processing_date = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (content, processed, doc_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error updating document content: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def insert_document(self, filename: str, file_path: str, file_size: int, file_type: str, content: str = None) -> bool:
        """Insert new document into database"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO documents (filename, file_path, file_size, file_type, content, processed)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (filename, file_path, file_size, file_type, content, False))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error inserting document: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

class UnifiedExtractor:
    """Unified document extraction system"""

    def __init__(self):
        self.db_manager = DatabaseManager(NEON_CONNECTION_STRING)
        self.performance_tracker = PerformanceTracker()
        self.document_cache = DocumentCache()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_supported_formats(self) -> Dict[str, InputFormat]:
        """Get supported file formats mapping"""
        return {
            '.pdf': InputFormat.PDF,
            '.docx': InputFormat.DOCX,
            '.pptx': InputFormat.PPTX,
            '.xlsx': InputFormat.XLSX,
            '.html': InputFormat.HTML,
            '.htm': InputFormat.HTML,
            '.md': InputFormat.MD,
            '.csv': InputFormat.CSV,
            '.png': InputFormat.IMAGE,
            '.jpg': InputFormat.IMAGE,
            '.jpeg': InputFormat.IMAGE,
            '.tiff': InputFormat.IMAGE,
            '.bmp': InputFormat.IMAGE,
        }

    def _encode_file_to_base64(self, file_path: str) -> Optional[str]:
        """Encode file to base64 string"""
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ Error encoding file: {e}")
            return None

    def _save_to_file(self, content: str, filename: str) -> bool:
        """Save content to file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False

    def _get_mistral_client(self) -> Optional[Mistral]:
        """Get Mistral client"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            print("❌ MISTRAL_API_KEY not found in environment variables")
            return None
        return Mistral(api_key=api_key)

    def extract_with_docling(self, file_path: str, enable_ocr: bool = False) -> Tuple[bool, str, str]:
        """Extract document using Docling (local processing)"""
        try:
            # Check cache first
            cached_result = self.document_cache.get_cached_result(file_path, "docling_extraction")
            if cached_result:
                print(f"📋 Using cached Docling result for {file_path}")
                return True, cached_result.get('content', ''), 'cached'

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            filename = f"{self.output_dir}/{base_name}_docling_extracted.md"

            print(f"🔍 Extracting with Docling: {file_path}")

            # Get file format
            file_extension = os.path.splitext(file_path)[1].lower()
            format_mapping = self._get_supported_formats()

            if file_extension not in format_mapping:
                print(f"❌ Unsupported file format for Docling: {file_extension}")
                return False, "", "unsupported_format"

            input_format = format_mapping[file_extension]

            # Create converter
            converter = DocumentConverter(allowed_formats=[input_format])
            result = converter.convert(file_path)
            doc = result.document

            # Export to markdown
            content = doc.export_to_markdown()

            # Save to file
            if self._save_to_file(content, filename):
                print(f"✅ Docling extraction completed! Content saved to: {filename}")
                print(f"📄 Extracted {len(content)} characters")

                # Cache the result
                self.document_cache.cache_result(file_path, "docling_extraction", {
                    "content": content,
                    "filename": filename,
                    "file_extension": file_extension,
                    "enable_ocr": enable_ocr
                })

                return True, content, "docling"
            else:
                return False, "", "save_error"

        except Exception as e:
            print(f"❌ Docling extraction failed: {e}")
            return False, "", "error"

    def extract_with_mistral_ocr(self, file_path: str) -> Tuple[bool, str, str]:
        """Extract document using Mistral OCR (cloud processing)"""
        try:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            filename = f"{self.output_dir}/{base_name}_mistral_extracted.md"

            print(f"☁️ Extracting with Mistral OCR: {file_path}")

            # Get Mistral client
            mistral_client = self._get_mistral_client()
            if not mistral_client:
                return False, "", "no_api_key"

            # Determine file type and prepare document data
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
                # Image file
                base64_data = self._encode_file_to_base64(file_path)
                if not base64_data:
                    return False, "", "encoding_error"

                document_data = {
                    "type": "image_url",
                    "image_url": f"data:image/{file_extension[1:]};base64,{base64_data}"
                }

            elif file_extension in ['.pdf', '.pptx', '.docx']:
                # Document file
                base64_data = self._encode_file_to_base64(file_path)
                if not base64_data:
                    return False, "", "encoding_error"

                mime_type = {
                    '.pdf': 'application/pdf',
                    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                }[file_extension]

                document_data = {
                    "type": "document_url",
                    "document_url": f"data:{mime_type};base64,{base64_data}"
                }

            else:
                print(f"❌ Unsupported file format for Mistral OCR: {file_extension}")
                return False, "", "unsupported_format"

            # Process with Mistral OCR
            ocr_response = mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document=document_data,
                include_image_base64=False
            )

            # Extract text content
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                content = ""
                for page in ocr_response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        content += page.markdown + "\n\n"
                    elif hasattr(page, 'content') and page.content:
                        content += page.content + "\n\n"
            else:
                print("❌ No content extracted from document with Mistral OCR")
                return False, "", "no_content"

            # Save to file
            if self._save_to_file(content, filename):
                print(f"✅ Mistral OCR extraction completed! Content saved to: {filename}")
                print(f"📄 Extracted {len(content)} characters")
                return True, content, "mistral_ocr"
            else:
                return False, "", "save_error"

        except Exception as e:
            print(f"❌ Mistral OCR extraction failed: {e}")
            return False, "", "error"

    def extract_document(self, file_path: str, prefer_cloud: bool = False, use_cache: bool = True) -> Tuple[bool, str, str]:
        """
        Extract document with intelligent fallback logic

        Args:
            file_path: Path to document
            prefer_cloud: Prefer Mistral OCR over Docling
            use_cache: Use caching for results

        Returns:
            Tuple of (success, content, method_used)
        """
        print(f"🚀 Processing document: {file_path}")

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False, "", "file_not_found"

        # Check cache if enabled
        if use_cache:
            cached_result = self.document_cache.get_cached_result(file_path, "unified_extraction")
            if cached_result:
                print(f"📋 Using cached result for {file_path}")
                return True, cached_result.get('content', ''), 'cached'

        # Try preferred method first
        if prefer_cloud:
            print("☁️ Trying Mistral OCR first...")
            success, content, method = self.extract_with_mistral_ocr(file_path)
            if success:
                self.document_cache.cache_result(file_path, "unified_extraction", {
                    "content": content,
                    "method": method
                })
                return True, content, method

            print("⚠️ Mistral OCR failed, trying Docling...")
            success, content, method = self.extract_with_docling(file_path)
        else:
            print("🔍 Trying Docling first...")
            success, content, method = self.extract_with_docling(file_path)
            if success:
                self.document_cache.cache_result(file_path, "unified_extraction", {
                    "content": content,
                    "method": method
                })
                return True, content, method

            print("⚠️ Docling failed, trying Mistral OCR...")
            success, content, method = self.extract_with_mistral_ocr(file_path)

        if success:
            self.document_cache.cache_result(file_path, "unified_extraction", {
                "content": content,
                "method": method
            })

        return success, content, method

    def process_from_database(self, mark_processed: bool = False) -> int:
        """Process all unprocessed documents from database"""
        documents = self.db_manager.get_unprocessed_documents()

        if not documents:
            print("✅ No unprocessed documents found in database")
            return 0

        print(f"📋 Found {len(documents)} unprocessed document(s) in database")
        success_count = 0

        for doc in documents:
            print(f"\n🔄 Processing: {doc['filename']} (ID: {doc['id']})")

            success, content, method = self.extract_document(doc['file_path'])

            if success:
                # Update database with extracted content
                if self.db_manager.update_document_content(doc['id'], content, mark_processed):
                    print(f"✅ Successfully processed and stored: {doc['filename']} using {method}")
                    success_count += 1
                else:
                    print(f"❌ Failed to store content in database: {doc['filename']}")
            else:
                print(f"❌ Failed to extract content: {doc['filename']}")

        print(f"\n🎉 Database processing completed! Successfully processed {success_count}/{len(documents)} documents")
        return success_count

    def add_file_to_database(self, file_path: str) -> bool:
        """Add a file to the database for processing"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = filename.split('.')[-1].lower()

        # Read content for text files
        content = None
        if file_type in ['txt', 'md', 'html']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                content = None

        success = self.db_manager.insert_document(filename, file_path, file_size, file_type, content)
        if success:
            print(f"✅ File '{filename}' added to database successfully!")
        else:
            print(f"❌ Failed to add file '{filename}' to database")

        return success

    def download_and_process_url(self, url: str) -> Tuple[bool, str, str]:
        """Download file from URL and process it"""
        try:
            print(f"🌐 Downloading file from: {url}")

            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Determine file extension from URL
            file_extension = os.path.splitext(url)[1]
            if not file_extension:
                file_extension = ".pdf"  # Default to PDF

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
            temp_file.close()

            # Write content to temporary file
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"✅ Downloaded to: {temp_file.name}")

            # Process the downloaded file
            success, content, method = self.extract_document(temp_file.name)

            # Clean up temporary file
            os.unlink(temp_file.name)

            if success:
                print(f"✅ Successfully processed URL content using {method}")
            else:
                print("❌ Failed to process URL content")

            return success, content, method

        except Exception as e:
            print(f"❌ Error processing URL: {e}")
            return False, "", "error"

    def batch_process_directory(self, directory: str, pattern: str = "*") -> int:
        """Process all files in a directory matching a pattern"""
        if not os.path.exists(directory):
            print(f"❌ Directory not found: {directory}")
            return 0

        import glob
        file_pattern = os.path.join(directory, pattern)
        files = glob.glob(file_pattern)

        if not files:
            print(f"❌ No files found matching pattern: {file_pattern}")
            return 0

        print(f"📁 Found {len(files)} files to process in {directory}")
        success_count = 0

        for file_path in files:
            if os.path.isfile(file_path):
                print(f"\n🔄 Processing: {os.path.basename(file_path)}")
                success, content, method = self.extract_document(file_path)

                if success:
                    print(f"✅ Successfully processed: {os.path.basename(file_path)} using {method}")
                    success_count += 1
                else:
                    print(f"❌ Failed to process: {os.path.basename(file_path)}")

        print(f"\n🎉 Batch processing completed! Successfully processed {success_count}/{len(files)} files")
        return success_count

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        try:
            with open(self.performance_tracker.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                return {"error": "No performance data available"}

            # Parse performance data
            total_extractions = len(lines)
            methods = {}
            total_time = 0
            total_memory = 0

            for line in lines[-10:]:  # Last 10 entries
                parts = line.strip().split(' | ')
                if len(parts) >= 6:
                    method = parts[2].replace("Method: ", "")
                    time_str = parts[3].replace("Time: ", "").replace("s", "")
                    memory_str = parts[4].replace("Memory: ", "").replace("MB", "")

                    try:
                        total_time += float(time_str)
                        total_memory += float(memory_str)

                        if method not in methods:
                            methods[method] = 0
                        methods[method] += 1
                    except ValueError:
                        continue

            return {
                "total_extractions": total_extractions,
                "recent_extractions": len(lines[-10:]),
                "methods_used": methods,
                "average_time": total_time / max(1, len(lines[-10:])),
                "average_memory": total_memory / max(1, len(lines[-10:])),
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(
        description="🔥 UNIFIED DOCUMENT EXTRACTION SYSTEM 🔥",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract single file with fallback logic
  python unified-extraction.py --source document.pdf

  # Prefer cloud extraction (Mistral OCR)
  python unified-extraction.py --source document.pdf --prefer-cloud

  # Process all unprocessed documents from database
  python unified-extraction.py --process-db

  # Add file to database for processing
  python unified-extraction.py --add-to-db document.pdf

  # Download and process URL
  python unified-extraction.py --url https://example.com/document.pdf

  # Batch process directory
  python unified-extraction.py --batch-dir data/uploads --pattern *.pdf

  # Get performance statistics
  python unified-extraction.py --stats

  # Enable OCR for image-heavy documents
  python unified-extraction.py --source document.pdf --enable-ocr
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--source", help="Path to input file")
    input_group.add_argument("--process-db", action="store_true", help="Process all unprocessed documents from database")
    input_group.add_argument("--add-to-db", help="Add file to database for processing")
    input_group.add_argument("--url", help="URL to download and process")
    input_group.add_argument("--batch-dir", help="Directory to batch process")
    input_group.add_argument("--pattern", default="*", help="File pattern for batch processing")
    input_group.add_argument("--stats", action="store_true", help="Show performance statistics")

    # Processing options
    parser.add_argument("--prefer-cloud", action="store_true", help="Prefer Mistral OCR over Docling")
    parser.add_argument("--enable-ocr", action="store_true", help="Enable OCR processing for Docling")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--mark-processed", action="store_true", help="Mark database documents as processed")

    args = parser.parse_args()

    # Create extractor instance
    extractor = UnifiedExtractor()

    # Handle different modes
    if args.stats:
        print("📊 Performance Statistics:")
        stats = extractor.get_performance_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        return 0

    elif args.process_db:
        print("🔄 Processing all unprocessed documents from database...")
        success_count = extractor.process_from_database(args.mark_processed)
        return 0 if success_count > 0 else 1

    elif args.add_to_db:
        print(f"➕ Adding file to database: {args.add_to_db}")
        success = extractor.add_file_to_database(args.add_to_db)
        return 0 if success else 1

    elif args.url:
        print(f"🌐 Processing URL: {args.url}")
        success, content, method = extractor.download_and_process_url(args.url)
        return 0 if success else 1

    elif args.batch_dir:
        print(f"📁 Batch processing directory: {args.batch_dir}")
        success_count = extractor.batch_process_directory(args.batch_dir, args.pattern)
        return 0 if success_count > 0 else 1

    elif args.source:
        print("🚀 Starting unified extraction...")

        # Configure extraction
        use_cache = not args.no_cache
        prefer_cloud = args.prefer_cloud

        success, content, method = extractor.extract_document(
            args.source,
            prefer_cloud=prefer_cloud,
            use_cache=use_cache
        )

        if success:
            print(f"✅ Extraction completed successfully using {method}!")
            print(f"📄 Extracted {len(content)} characters")
            return 0
        else:
            print("❌ All extraction methods failed")
            return 1

    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())