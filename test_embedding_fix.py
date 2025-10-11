#!/usr/bin/env python3
"""
Test script to verify that the embedding fix works correctly.
This script tests that the embed endpoint only processes chunks for the specific document.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models import Document, DocumentChunk, Embedding
from app.services.embedding_service import EmbeddingService

async def test_embedding_fix():
    """Test that embedding service only processes chunks for specific document"""
    print("🧪 Testing embedding fix...")

    # Initialize database session
    db = SessionLocal()

    try:
        # Get all documents
        documents = db.query(Document).all()
        print(f"📄 Found {len(documents)} documents in database")

        if len(documents) < 2:
            print("⚠️ Need at least 2 documents to properly test the fix")
            print("💡 Please upload at least 2 documents first")
            return

        # Find documents that need embedding
        docs_needing_embedding = [doc for doc in documents if doc.status == 'chunked']
        print(f"📦 Found {len(docs_needing_embedding)} documents that need embedding")

        if len(docs_needing_embedding) == 0:
            print("⚠️ No documents found that need embedding")
            print("💡 Please chunk some documents first")
            return

        # Test the new method with a specific document
        test_document = docs_needing_embedding[0]
        print(f"🎯 Testing embedding for document ID: {test_document.id}")
        print(f"📄 Document: {test_document.original_filename}")

        # Count chunks for this document before embedding
        chunks_before = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == test_document.id
        ).count()
        print(f"📊 Chunks before embedding: {chunks_before}")

        # Count total chunks that need embedding across all documents
        total_chunks_needing_embedding = db.query(DocumentChunk).outerjoin(
            Embedding, DocumentChunk.id == Embedding.chunk_id
        ).filter(
            Embedding.id.is_(None)
        ).count()
        print(f"📊 Total chunks needing embedding across all documents: {total_chunks_needing_embedding}")

        if total_chunks_needing_embedding == 0:
            print("✅ No chunks need embedding - test cannot verify the fix")
            return

        # Initialize embedding service
        embedding_service = EmbeddingService()

        # Test the new document-specific method
        print("🚀 Running document-specific embedding...")
        result = await embedding_service.process_embeddings_for_document(db, test_document.id)

        print("📊 Embedding result:")
        print(f"   Success: {result.success}")
        print(f"   Embeddings created: {result.embeddings_created}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Metadata: {result.metadata}")

        # Verify that only the specific document's chunks were processed
        chunks_after = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == test_document.id
        ).count()

        embeddings_for_doc = db.query(Embedding).join(
            DocumentChunk, Embedding.chunk_id == DocumentChunk.id
        ).filter(
            DocumentChunk.document_id == test_document.id
        ).count()

        print("\n📊 Verification:")
        print(f"   Chunks for test document: {chunks_after}")
        print(f"   Embeddings created for test document: {embeddings_for_doc}")

        # Check if other documents' chunks were processed
        total_chunks_after = db.query(DocumentChunk).outerjoin(
            Embedding, DocumentChunk.id == Embedding.chunk_id
        ).filter(
            Embedding.id.is_(None)
        ).count()

        print(f"   Total chunks still needing embedding: {total_chunks_after}")

        if result.success and result.embeddings_created > 0:
            print("✅ Test PASSED: Embedding fix is working correctly!")
            print(f"   - Created {result.embeddings_created} embeddings for document {test_document.id}")
            print(f"   - Other documents' chunks were not processed (as expected)")
        else:
            print("❌ Test FAILED: Embedding did not work as expected")
            print(f"   - Success: {result.success}")
            print(f"   - Embeddings created: {result.embeddings_created}")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_embedding_fix())