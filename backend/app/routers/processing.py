"""
Document Processing Router

This router provides API endpoints for document processing operations:
- Document extraction
- Document chunking
- Embedding creation
- Processing status and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime
import os

from ..database import get_db
from ..models import User, Document, DocumentChunk, Embedding
from ..schemas import ProcessingStatus, ProcessingResult
from ..auth import get_current_active_user
from ..services import DocumentProcessor, DocumentChunker, EmbeddingService

router = APIRouter()

# Initialize services
document_processor = DocumentProcessor()
document_chunker = DocumentChunker()
embedding_service = EmbeddingService()

@router.post("/{document_id}/extract", response_model=ProcessingResult)
async def extract_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Extract content from uploaded document"""
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document file not found on disk"
        )

    # Update document status to processing
    document.status = "processing"
    db.commit()

    try:
        # Process document extraction
        result = await document_processor.extract_document(document.file_path)

        if result.success:
            # Update document with extracted content
            document.content = result.content
            document.status = "extracted"
            document.processed_at = datetime.utcnow()
            db.commit()

            return ProcessingResult(
                success=True,
                message=f"Document extracted successfully using {result.method}",
                processing_time=result.processing_time,
                metadata=result.metadata
            )
        else:
            document.status = "failed"
            db.commit()

            return ProcessingResult(
                success=False,
                message=f"Document extraction failed: {result.method}",
                processing_time=result.processing_time,
                metadata={"error": result.method}
            )

    except Exception as e:
        document.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document extraction failed: {str(e)}"
        )

@router.post("/{document_id}/chunk", response_model=ProcessingResult)
async def chunk_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Split document into searchable chunks"""
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not document.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extracted content. Please extract first."
        )

    # Update document status to processing
    document.status = "processing"
    db.commit()

    try:
        # Process document chunking
        result = await document_chunker.process_document_from_db(db, document_id)

        if result.success:
            return ProcessingResult(
                success=True,
                message=f"Document chunked successfully. Created {result.chunks_created} chunks.",
                processing_time=result.processing_time,
                metadata=result.metadata
            )
        else:
            document.status = "failed"
            db.commit()

            return ProcessingResult(
                success=False,
                message="Document chunking failed",
                processing_time=result.processing_time,
                metadata=result.metadata
            )

    except Exception as e:
        document.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document chunking failed: {str(e)}"
        )

@router.post("/{document_id}/embed", response_model=ProcessingResult)
async def create_embeddings(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create embeddings for document chunks"""
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Check if document has chunks
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).count()

    if chunk_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no chunks. Please chunk the document first."
        )

    # Update document status to processing
    document.status = "processing"
    db.commit()

    try:
        # Process embeddings
        result = await embedding_service.process_embeddings_from_db(db)

        if result.success:
            # Update document status to completed
            document.status = "processed"
            document.processed_at = datetime.utcnow()
            db.commit()

            return ProcessingResult(
                success=True,
                message=f"Embeddings created successfully. Processed {result.embeddings_created} chunks.",
                processing_time=result.processing_time,
                metadata=result.metadata
            )
        else:
            document.status = "failed"
            db.commit()

            return ProcessingResult(
                success=False,
                message="Embedding creation failed",
                processing_time=result.processing_time,
                metadata=result.metadata
            )

    except Exception as e:
        document.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding creation failed: {str(e)}"
        )

@router.post("/{document_id}/process", response_model=ProcessingResult)
async def process_document_complete(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete document processing pipeline: Extract → Chunk → Embed"""
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document file not found on disk"
        )

    # Update document status to processing
    document.status = "processing"
    db.commit()

    try:
        # Step 1: Extract document content
        extraction_result = await document_processor.extract_document(document.file_path)

        if not extraction_result.success:
            document.status = "failed"
            db.commit()
            return ProcessingResult(
                success=False,
                message=f"Document extraction failed: {extraction_result.method}",
                processing_time=extraction_result.processing_time,
                metadata={"error": extraction_result.method}
            )

        # Update document with extracted content
        document.content = extraction_result.content
        document.status = "extracted"
        db.commit()

        # Step 2: Chunk the document
        chunking_result = await document_chunker.process_document_from_db(db, document_id)

        if not chunking_result.success:
            document.status = "failed"
            db.commit()
            return ProcessingResult(
                success=False,
                message="Document chunking failed",
                processing_time=extraction_result.processing_time + chunking_result.processing_time,
                metadata={"error": "chunking_failed"}
            )

        # Step 3: Create embeddings
        embedding_result = await embedding_service.process_embeddings_from_db(db)

        if not embedding_result.success:
            document.status = "failed"
            db.commit()
            return ProcessingResult(
                success=False,
                message="Embedding creation failed",
                processing_time=extraction_result.processing_time + chunking_result.processing_time + embedding_result.processing_time,
                metadata={"error": "embedding_failed"}
            )

        # All steps successful
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()

        return ProcessingResult(
            success=True,
            message=f"Document fully processed! Extracted → Chunked ({chunking_result.chunks_created} chunks) → Embedded ({embedding_result.embeddings_created} embeddings)",
            processing_time=extraction_result.processing_time + chunking_result.processing_time + embedding_result.processing_time,
            metadata={
                "extraction_method": extraction_result.method,
                "chunks_created": chunking_result.chunks_created,
                "embeddings_created": embedding_result.embeddings_created
            }
        )

    except Exception as e:
        document.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

@router.get("/{document_id}/status", response_model=ProcessingStatus)
async def get_processing_status(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document processing status"""
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Get chunk and embedding counts
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).count()

    embedding_count = db.query(Embedding).join(
        DocumentChunk, Embedding.chunk_id == DocumentChunk.id
    ).filter(
        DocumentChunk.document_id == document_id
    ).count()

    return ProcessingStatus(
        document_id=document_id,
        status=document.status,
        content_length=len(document.content) if document.content else 0,
        chunks_count=chunk_count,
        embeddings_count=embedding_count,
        created_at=document.created_at,
        processed_at=document.processed_at
    )

@router.post("/batch/process", response_model=ProcessingResult)
async def batch_process_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process all unprocessed documents for the current user"""
    # Get user's unprocessed documents
    documents = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.status.in_(["not processed", "extracted", "chunked"])
    ).all()

    if not documents:
        return ProcessingResult(
            success=True,
            message="No documents need processing",
            processing_time=0.0,
            metadata={"processed_count": 0}
        )

    processed_count = 0
    total_time = 0

    for document in documents:
        try:
            # Process each document completely
            result = await process_document_complete(document.id, current_user, db)

            if result.success:
                processed_count += 1
                total_time += result.processing_time

        except Exception as e:
            print(f"Failed to process document {document.filename}: {e}")
            continue

    return ProcessingResult(
        success=processed_count > 0,
        message=f"Batch processing completed. Successfully processed {processed_count}/{len(documents)} documents.",
        processing_time=total_time,
        metadata={
            "total_documents": len(documents),
            "processed_count": processed_count,
            "failed_count": len(documents) - processed_count
        }
    )