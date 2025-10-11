from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import logging
import os

from .database import SessionLocal
from .services.document_processor import DocumentProcessor
from .services.document_chunker import DocumentChunker
from .services.embedding_service import EmbeddingService
from .models import Document

# Synchronous task processing (Redis/Celery removed)
# Tasks will now run synchronously instead of in background

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_document_task(document_id: int):
    """Background task for complete document processing pipeline"""
    db = SessionLocal()
    try:
        logger.info(f"Starting background processing for document {document_id}")

        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"success": False, "error": "Document not found"}

        # Update status to processing
        document.status = "processing"
        db.commit()
        logger.info(f"Document {document_id} status updated to processing")

        # Step 1: Extract content
        try:
            logger.info(f"Starting extraction for document {document_id}")
            processor = DocumentProcessor()
            result = asyncio.run(processor.extract_document(document.file_path))

            if result.success:
                document.content = result.content
                document.status = "extracted"
                db.commit()
                logger.info(f"Document {document_id} extracted successfully")
            else:
                raise Exception(f"Extraction failed: {result.method}")

        except Exception as e:
            logger.error(f"Extraction failed for document {document_id}: {str(e)}")
            document.status = "error"
            db.commit()
            return {"success": False, "error": f"Extraction failed: {str(e)}"}

        # Step 2: Chunk document
        try:
            logger.info(f"Starting chunking for document {document_id}")
            chunker = DocumentChunker()
            chunk_result = asyncio.run(chunker.process_document_from_db(db, document_id))

            if chunk_result.success:
                document.status = "chunked"
                db.commit()
                logger.info(f"Document {document_id} chunked successfully")
            else:
                raise Exception(f"Chunking failed: {chunk_result.metadata.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Chunking failed for document {document_id}: {str(e)}")
            document.status = "error"
            db.commit()
            return {"success": False, "error": f"Chunking failed: {str(e)}"}

        # Step 3: Generate embeddings
        try:
            logger.info(f"Starting embedding generation for document {document_id}")
            embedding_service = EmbeddingService()
            embed_result = asyncio.run(
                embedding_service.process_embeddings_for_document(db, document_id)
            )

            if embed_result.success:
                document.status = "embedding"
                document.processed_at = datetime.utcnow()
                db.commit()
                logger.info(f"Document {document_id} processed successfully")
                return {"success": True, "message": "Document processed successfully"}
            else:
                raise Exception(f"Embedding failed: {embed_result.metadata.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Embedding failed for document {document_id}: {str(e)}")
            document.status = "error"
            db.commit()
            return {"success": False, "error": f"Embedding failed: {str(e)}"}

    except Exception as e:
        logger.error(f"Unexpected error processing document {document_id}: {str(e)}")
        if 'document' in locals():
            document.status = "error"
            db.commit()
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
    finally:
        db.close()

def extract_document_task(document_id: int):
    """Background task for document extraction only"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"success": False, "error": "Document not found"}

        document.status = "processing"
        db.commit()

        processor = DocumentProcessor()
        result = asyncio.run(processor.extract_document(document.file_path))

        if result.success:
            document.content = result.content
            document.status = "extracted"
            document.processed_at = datetime.utcnow()
            db.commit()
            return {"success": True, "method": result.method}
        else:
            document.status = "error"
            db.commit()
            return {"success": False, "error": f"Extraction failed: {result.method}"}

    except Exception as e:
        document.status = "error"
        db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def chunk_document_task(document_id: int):
    """Background task for document chunking only"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"success": False, "error": "Document not found"}

        if not document.content:
            return {"success": False, "error": "Document has no extracted content"}

        chunker = DocumentChunker()
        result = asyncio.run(chunker.process_document_from_db(db, document_id))

        if result.success:
            document.status = "chunked"
            db.commit()
            return {"success": True, "chunks_created": result.chunks_created}
        else:
            document.status = "error"
            db.commit()
            return {"success": False, "error": "Chunking failed"}

    except Exception as e:
        document.status = "error"
        db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def embed_document_task(document_id: int):
    """Background task for embedding generation only"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"success": False, "error": "Document not found"}

        # Check if document has chunks
        from .models import DocumentChunk
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).count()

        if chunk_count == 0:
            return {"success": False, "error": "Document has no chunks"}

        embedding_service = EmbeddingService()
        result = asyncio.run(embedding_service.process_embeddings_for_document(db, document_id))

        if result.success:
            document.status = "embedding"
            document.processed_at = datetime.utcnow()
            db.commit()
            return {"success": True, "embeddings_created": result.embeddings_created}
        else:
            document.status = "error"
            db.commit()
            return {"success": False, "error": "Embedding generation failed"}

    except Exception as e:
        document.status = "error"
        db.commit()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def cleanup_temp_files_task():
    """Background task to clean up temporary files"""
    try:
        temp_dir = "/tmp"
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                if file.startswith("temp_") or file.endswith(".tmp"):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        os.remove(file_path)
                        logger.info(f"Cleaned up temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file {file_path}: {e}")

        return {"success": True, "message": "Cleanup completed"}
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {"success": False, "error": str(e)}