"""
Document Processing Services

This module contains all the core services for document processing:
- Document extraction (replacing 1-extraction.py)
- Document chunking (replacing 2-chunking-neon.py)
- Embedding creation (replacing 3-embedding-neon.py)
"""

from .document_processor import DocumentProcessor
from .document_chunker import DocumentChunker
from .embedding_service import EmbeddingService

__all__ = [
    "DocumentProcessor",
    "DocumentChunker",
    "EmbeddingService"
]