import magic
import hashlib
import os
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class FileSecurity:
    def __init__(self):
        from .config import settings
        
        # Map file extensions to MIME types
        self.extension_to_mime = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'ppt': 'application/vnd.ms-powerpoint',
            'odt': 'application/vnd.oasis.opendocument.text',
            'ods': 'application/vnd.oasis.opendocument.spreadsheet',
            'odp': 'application/vnd.oasis.opendocument.presentation',
            'rtf': 'application/rtf',
            'md': 'text/markdown',
            'html': 'text/html',
            'htm': 'text/html',
            'txt': 'text/plain',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'tiff': 'image/tiff',
            'bmp': 'image/bmp',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'csv': 'text/csv',
            'tsv': 'text/tab-separated-values',
            'xml': 'application/xml',
            'json': 'application/json',
            'epub': 'application/epub+zip'
        }
        
        # Build allowed MIME types from configuration
        self.allowed_mime_types = set()
        for ext in settings.allowed_extensions:
            if ext in self.extension_to_mime:
                self.allowed_mime_types.add(self.extension_to_mime[ext])

        # Dangerous file signatures (magic numbers)
        self.dangerous_signatures = {
            b'\x4D\x5A': 'Windows executable',  # MZ header
            b'\x7F\x45\x4C\x46': 'ELF executable',  # ELF header
            b'\xCA\xFE\xBA\xBE': 'Java class file',  # Java class
            b'\xFE\xED\xFA': 'Mach-O binary',  # Mach-O binary (macOS/iOS)
        }

        # Maximum file sizes by type (in bytes)
        self.max_sizes = {
            'application/pdf': 50 * 1024 * 1024,  # 50MB for PDFs
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 20 * 1024 * 1024,  # 20MB for DOCX
            'application/msword': 20 * 1024 * 1024,  # 20MB for DOC
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 50 * 1024 * 1024,  # 50MB for XLSX
            'application/vnd.ms-excel': 50 * 1024 * 1024,  # 50MB for XLS
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 50 * 1024 * 1024,  # 50MB for PPTX
            'application/vnd.ms-powerpoint': 50 * 1024 * 1024,  # 50MB for PPT
            'application/vnd.oasis.opendocument.text': 20 * 1024 * 1024,  # 20MB for ODT
            'application/vnd.oasis.opendocument.spreadsheet': 50 * 1024 * 1024,  # 50MB for ODS
            'application/vnd.oasis.opendocument.presentation': 50 * 1024 * 1024,  # 50MB for ODP
            'application/rtf': 10 * 1024 * 1024,  # 10MB for RTF
            'text/markdown': 5 * 1024 * 1024,     # 5MB for MD
            'text/html': 10 * 1024 * 1024,        # 10MB for HTML
            'text/plain': 5 * 1024 * 1024,        # 5MB for TXT
            'image/png': 20 * 1024 * 1024,       # 20MB for PNG
            'image/jpeg': 20 * 1024 * 1024,      # 20MB for JPEG
            'image/tiff': 100 * 1024 * 1024,     # 100MB for TIFF
            'image/bmp': 50 * 1024 * 1024,       # 50MB for BMP
            'image/gif': 20 * 1024 * 1024,       # 20MB for GIF
            'image/svg+xml': 5 * 1024 * 1024,    # 5MB for SVG
            'text/csv': 10 * 1024 * 1024,        # 10MB for CSV
            'text/tab-separated-values': 10 * 1024 * 1024,  # 10MB for TSV
            'application/xml': 10 * 1024 * 1024, # 10MB for XML
            'application/json': 10 * 1024 * 1024, # 10MB for JSON
            'application/epub+zip': 100 * 1024 * 1024,  # 100MB for EPUB
            'default': 10 * 1024 * 1024          # 10MB default
        }

    def validate_file_content(self, file_path: str) -> bool:
        """Comprehensive file content validation"""
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return False

            file_size = Path(file_path).stat().st_size

            # Check for empty files
            if file_size == 0:
                logger.warning(f"Empty file detected: {file_path}")
                return False

            # Check for unusually small files (potential zip bombs or malformed files)
            if file_size < 100:
                logger.warning(f"Unusually small file: {file_path} ({file_size} bytes)")
                return False

            # Detect MIME type using magic numbers
            mime = magic.Magic(mime=True)
            detected_type = mime.from_file(file_path)

            if detected_type not in self.allowed_mime_types:
                logger.warning(f"Disallowed MIME type: {detected_type} for file {file_path}")
                return False

            # Additional security checks based on file type
            if not self._validate_file_structure(file_path, detected_type):
                return False

            # Check for compression bombs
            if self._is_compression_bomb(file_path, detected_type):
                logger.warning(f"Potential compression bomb detected: {file_path}")
                return False

            # Check file size against type-specific limits
            max_size = self.max_sizes.get(detected_type, self.max_sizes['default'])
            if file_size > max_size:
                logger.warning(f"File too large: {file_path} ({file_size} bytes > {max_size} bytes)")
                return False

            logger.info(f"File validation passed: {file_path} ({detected_type})")
            return True

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {str(e)}")
            return False

    def _validate_file_structure(self, file_path: str, mime_type: str) -> bool:
        """Validate file structure based on MIME type"""
        try:
            # Read first 64 bytes for signature checking
            with open(file_path, 'rb') as f:
                header = f.read(64)

            # Check for dangerous file signatures
            for signature, description in self.dangerous_signatures.items():
                if header.startswith(signature):
                    logger.warning(f"Dangerous file signature detected: {description}")
                    return False

            # Type-specific validations
            if mime_type == 'application/pdf':
                return self._validate_pdf_structure(header)
            elif mime_type.startswith('image/'):
                return self._validate_image_structure(header, mime_type)
            elif mime_type in ['text/markdown', 'text/html', 'text/plain', 'text/csv', 'text/tab-separated-values']:
                return self._validate_text_structure(file_path)
            elif mime_type in ['application/xml', 'application/json']:
                return self._validate_structured_text_structure(file_path)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                              'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                              'application/epub+zip']:
                # These are ZIP-based formats, basic validation
                return self._validate_zip_based_structure(header)
            elif mime_type in ['application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint',
                              'application/rtf', 'application/vnd.oasis.opendocument.text',
                              'application/vnd.oasis.opendocument.spreadsheet', 'application/vnd.oasis.opendocument.presentation']:
                # Legacy/binary formats, basic validation
                return self._validate_binary_document_structure(header)

            return True

        except Exception as e:
            logger.error(f"Error validating file structure: {str(e)}")
            return False

    def _validate_pdf_structure(self, header: bytes) -> bool:
        """Validate PDF file structure"""
        # Check for PDF header
        if not header.startswith(b'%PDF-'):
            return False

        # Check for proper PDF version
        try:
            version_line = header.split(b'\n')[0] if b'\n' in header else header
            if not version_line.startswith(b'%PDF-'):
                return False
        except:
            return False

        return True

    def _validate_image_structure(self, header: bytes, mime_type: str) -> bool:
        """Validate image file structure"""
        # PNG validation
        if mime_type == 'image/png':
            if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                return False

        # JPEG validation
        elif mime_type == 'image/jpeg':
            if not (header.startswith(b'\xFF\xD8\xFF') and b'\xFF\xD9' in header[-10:]):
                return False

        # TIFF validation
        elif mime_type == 'image/tiff':
            if not (header.startswith(b'II*\x00') or header.startswith(b'MM\x00*')):
                return False

        # BMP validation
        elif mime_type == 'image/bmp':
            if not header.startswith(b'BM'):
                return False

        return True

    def _validate_text_structure(self, file_path: str) -> bool:
        """Validate text file structure"""
        try:
            with open(file_path, 'rb') as f:
                # Read first 1KB for analysis
                sample = f.read(1024)

            # Check for null bytes (indicates binary content)
            if b'\x00' in sample:
                return False

            # Check for extremely high entropy (might indicate encrypted/compressed content)
            if self._calculate_entropy(sample) > 7.5:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating text structure: {str(e)}")
            return False

    def _is_compression_bomb(self, file_path: str, mime_type: str) -> bool:
        """Detect potential compression bombs"""
        try:
            file_size = Path(file_path).stat().st_size

            # For now, implement basic size checks
            # Advanced compression bomb detection would require more sophisticated analysis

            # PDFs over 40MB might be problematic
            if mime_type == 'application/pdf' and file_size > 40 * 1024 * 1024:
                return True

            # Images over 15MB might be problematic
            if mime_type.startswith('image/') and file_size > 15 * 1024 * 1024:
                return True

            return False

        except Exception:
            return False

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if len(data) == 0:
            return 0.0

        entropy = 0.0
        byte_counts = [0] * 256

        for byte in data:
            byte_counts[byte] += 1

        for count in byte_counts:
            if count > 0:
                probability = count / len(data)
                entropy -= probability * (probability).bit_length()

        return entropy

    def _validate_structured_text_structure(self, file_path: str) -> bool:
        """Validate structured text files (XML, JSON)"""
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
            
            # Check for null bytes
            if b'\x00' in sample:
                return False
            
            # Basic validation - check if it starts with common patterns
            if sample.strip().startswith(b'<?xml') or sample.strip().startswith(b'<'):
                # XML-like structure
                return True
            elif sample.strip().startswith(b'{') or sample.strip().startswith(b'['):
                # JSON-like structure
                return True
            
            return True  # Allow other structured text formats
        except Exception as e:
            logger.error(f"Error validating structured text: {str(e)}")
            return False

    def _validate_zip_based_structure(self, header: bytes) -> bool:
        """Validate ZIP-based formats (DOCX, XLSX, PPTX, EPUB)"""
        # ZIP files start with PK header
        return header.startswith(b'PK')

    def _validate_binary_document_structure(self, header: bytes) -> bool:
        """Validate binary document formats (DOC, XLS, PPT, RTF, ODF)"""
        # Basic validation - check for common document signatures
        # RTF files start with {\rtf
        if header.startswith(b'{\\rtf'):
            return True
        # ODF files are ZIP-based
        if header.startswith(b'PK'):
            return True
        # Legacy MS Office formats have specific signatures
        if header.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):  # MS Compound Document
            return True
        
        # Allow other binary formats with basic validation
        return len(header) > 0

    def scan_for_malware_signatures(self, file_path: str) -> bool:
        """Scan for known malware signatures"""
        try:
            # This is a basic implementation
            # In production, you would use a proper antivirus SDK or service

            with open(file_path, 'rb') as f:
                content = f.read()

            # Check for some common malware patterns (basic example)
            suspicious_patterns = [
                b'powershell.exe -encodedcommand',
                b'cmd.exe /c',
                b'script.exe',
                b'javascript:vbscript',
            ]

            for pattern in suspicious_patterns:
                if pattern.lower() in content.lower():
                    logger.warning(f"Potential malware pattern detected in {file_path}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error scanning for malware: {str(e)}")
            return False

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {str(e)}")
            return ""

def validate_upload_file_sync(file: UploadFile, security: FileSecurity) -> tuple[bool, str]:
    """Synchronous file validation for uploaded files"""
    try:
        # Save file temporarily
        temp_path = f"/tmp/temp_{uuid.uuid4()}_{file.filename}"

        with open(temp_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        # Validate file
        is_valid = security.validate_file_content(temp_path)

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        if is_valid:
            return True, "File validation passed"
        else:
            return False, "File validation failed"

    except Exception as e:
        return False, f"Validation error: {str(e)}"

# Global security instance
file_security = FileSecurity()