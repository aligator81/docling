from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import logging
import os
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Callable
import json
from dataclasses import dataclass, asdict
from enum import Enum

from .database import SessionLocal
from .services.document_processor import DocumentProcessor
from .services.document_chunker import DocumentChunker
from .services.embedding_service import EmbeddingService
from .models import Document

# Async Background Processing System for Concurrent Document Processing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingJob:
    """Represents a document processing job"""
    document_id: int
    user_id: int
    filename: str
    priority: int = 1  # Higher number = higher priority
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    status: ProcessingStatus = ProcessingStatus.QUEUED
    current_step: str = ""
    progress: int = 0
    error_message: str = ""
    result: Dict = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class BackgroundTaskManager:
    """Manages background document processing tasks with concurrency control"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.processing_queue = queue.PriorityQueue()
        self.active_jobs: Dict[int, ProcessingJob] = {}
        self.completed_jobs: Dict[int, ProcessingJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.shutdown_event = threading.Event()
        self.worker_threads: List[threading.Thread] = []

        # Start worker threads
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.worker_threads.append(worker)

        logger.info(f"🚀 BackgroundTaskManager started with {max_workers} workers")

    def _worker_loop(self):
        """Main worker loop for processing documents"""
        while not self.shutdown_event.is_set():
            try:
                # Get next job from queue with timeout
                try:
                    priority, job = self.processing_queue.get(timeout=1)
                except queue.Empty:
                    continue

                if job is None:
                    break

                self._process_job(job)

            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                time.sleep(1)

    def _process_job(self, job: ProcessingJob):
        """Process a single document job"""
        try:
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.utcnow()
            self.active_jobs[job.document_id] = job

            logger.info(f"🔄 Starting processing job for document {job.document_id}")

            # Execute the full processing pipeline
            result = asyncio.run(self._execute_processing_pipeline(job))

            job.completed_at = datetime.utcnow()
            job.result = result

            if result.get("success", False):
                job.status = ProcessingStatus.COMPLETED
                logger.info(f"✅ Completed processing job for document {job.document_id}")
            else:
                job.status = ProcessingStatus.FAILED
                job.error_message = result.get("error", "Unknown error")
                logger.error(f"❌ Failed processing job for document {job.document_id}: {job.error_message}")

        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            logger.error(f"❌ Exception in processing job {job.document_id}: {e}")
        finally:
            # Move from active to completed
            if job.document_id in self.active_jobs:
                del self.active_jobs[job.document_id]
            self.completed_jobs[job.document_id] = job

    async def _execute_processing_pipeline(self, job: ProcessingJob) -> Dict:
        """Execute the complete document processing pipeline"""
        db = SessionLocal()

        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == job.document_id).first()
            if not document:
                return {"success": False, "error": "Document not found"}

            # Check if file exists
            if not os.path.exists(document.file_path):
                return {"success": False, "error": "Document file not found"}

            # Step 1: Extract content
            job.current_step = "extraction"
            job.progress = 10
            logger.info(f"📝 Step 1: Extracting content for document {job.document_id}")

            processor = DocumentProcessor()
            extract_result = await processor.extract_document(document.file_path)

            if not extract_result.success:
                return {"success": False, "error": f"Extraction failed: {extract_result.method}"}

            # Update document
            document.content = extract_result.content
            document.status = "extracted"
            db.commit()

            # Step 2: Chunk document
            job.current_step = "chunking"
            job.progress = 40
            logger.info(f"✂️ Step 2: Chunking document {job.document_id}")

            chunker = DocumentChunker()
            chunk_result = await chunker.process_document_from_db(db, job.document_id)

            if not chunk_result.success:
                return {"success": False, "error": f"Chunking failed: {chunk_result.metadata.get('error', 'Unknown error')}"}

            # Update document status
            document.status = "chunked"
            db.commit()

            # Step 3: Generate embeddings
            job.current_step = "embedding"
            job.progress = 70
            logger.info(f"🧠 Step 3: Generating embeddings for document {job.document_id}")

            embedding_service = EmbeddingService()
            embed_result = await embedding_service.process_embeddings_for_document(db, job.document_id)

            if not embed_result.success:
                return {"success": False, "error": f"Embedding failed: {embed_result.metadata.get('error', 'Unknown error')}"}

            # Final update
            document.status = "processed"
            document.processed_at = datetime.utcnow()
            db.commit()

            job.progress = 100
            return {
                "success": True,
                "extraction_method": extract_result.method,
                "chunks_created": chunk_result.chunks_created,
                "embeddings_created": embed_result.embeddings_created,
                "processing_time": (datetime.utcnow() - job.started_at).total_seconds()
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Pipeline error for document {job.document_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def add_job(self, document_id: int, user_id: int, filename: str, priority: int = 1) -> str:
        """Add a document processing job to the queue"""
        job = ProcessingJob(
            document_id=document_id,
            user_id=user_id,
            filename=filename,
            priority=priority
        )

        self.processing_queue.put((-priority, job))  # Negative for max-heap behavior
        logger.info(f"➕ Added processing job for document {document_id} with priority {priority}")
        return f"job_{document_id}_{int(time.time())}"

    def get_job_status(self, document_id: int) -> Optional[Dict]:
        """Get the status of a processing job"""
        # Check active jobs
        if document_id in self.active_jobs:
            job = self.active_jobs[document_id]
            return {
                "document_id": job.document_id,
                "status": job.status.value,
                "current_step": job.current_step,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None
            }

        # Check completed jobs
        if document_id in self.completed_jobs:
            job = self.completed_jobs[document_id]
            return {
                "document_id": job.document_id,
                "status": job.status.value,
                "current_step": job.current_step,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "result": job.result
            }

        return None

    def get_queue_stats(self) -> Dict:
        """Get statistics about the processing queue"""
        return {
            "queue_size": self.processing_queue.qsize(),
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.completed_jobs),
            "max_workers": self.max_workers
        }

    def shutdown(self):
        """Shutdown the background task manager"""
        logger.info("🛑 Shutting down BackgroundTaskManager")
        self.shutdown_event.set()

        # Add sentinel values to wake up workers
        for _ in range(self.max_workers):
            self.processing_queue.put((0, None))

        # Wait for workers to finish
        for worker in self.worker_threads:
            worker.join(timeout=5)

        self.executor.shutdown(wait=True)
        logger.info("✅ BackgroundTaskManager shutdown complete")

# Global background task manager instance
background_task_manager = BackgroundTaskManager(max_workers=3)

# Updated task functions using the new background processing system

def process_document_task(document_id: int):
    """Add document processing task to background queue"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"success": False, "error": "Document not found"}

        # Add to background processing queue
        background_task_manager.add_job(
            document_id=document_id,
            user_id=document.user_id,
            filename=document.original_filename
        )

        # Update initial status
        document.status = "queued"
        db.commit()

        return {"success": True, "message": "Document queued for background processing"}

    except Exception as e:
        logger.error(f"Error queuing document {document_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

def extract_document_task(document_id: int):
    """Legacy function - now uses background processing"""
    return process_document_task(document_id)

def chunk_document_task(document_id: int):
    """Legacy function - now uses background processing"""
    return process_document_task(document_id)

def embed_document_task(document_id: int):
    """Legacy function - now uses background processing"""
    return process_document_task(document_id)

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

# New functions for the background processing system

def get_processing_status(document_id: int) -> Optional[Dict]:
    """Get the processing status of a document"""
    return background_task_manager.get_job_status(document_id)

def get_queue_statistics() -> Dict:
    """Get statistics about the processing queue"""
    return background_task_manager.get_queue_stats()

def shutdown_background_processing():
    """Shutdown the background processing system"""
    background_task_manager.shutdown()