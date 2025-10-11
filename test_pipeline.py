#!/usr/bin/env python3
"""
Test script to verify the document processing pipeline
"""
import asyncio
import os
import sys
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models import Document, DocumentChunk, User
from app.services.document_processor import DocumentProcessor
from app.services.document_chunker import DocumentChunker

async def test_pipeline():
    """Test the document processing pipeline"""
    print("🚀 Testing document processing pipeline...")

    # Initialize database session
    db = SessionLocal()

    try:
        # Get test user
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            print("❌ Test user not found")
            return False

        print(f"✅ Found test user: {user.username} (ID: {user.id})")

        # Get the test document
        document = db.query(Document).filter(Document.id == 29).first()
        if not document:
            print("❌ Test document not found")
            return False

        print(f"📄 Test document: {document.filename} (ID: {document.id})")
        print(f"📊 Current status: {document.status}")
        print(f"📊 Current content length: {len(document.content) if document.content else 0}")

        # Test extraction
        print("\n🔍 Testing document extraction...")
        processor = DocumentProcessor()

        # Reset document status for testing
        document.status = "not processed"
        document.content = None
        db.commit()

        # Fix file path if needed
        file_path = document.file_path
        if not os.path.exists(file_path):
            # Try with backend prefix
            backend_file_path = os.path.join("backend", file_path)
            if os.path.exists(backend_file_path):
                file_path = backend_file_path
            else:
                print(f"❌ File not found: {file_path} or {backend_file_path}")
                return False

        result = await processor.extract_document(file_path)

        if result.success:
            print(f"✅ Extraction successful using {result.method}")
            print(f"📝 Content length: {len(result.content)} characters")
            print(f"⏱️ Processing time: {result.processing_time:.2f} seconds")

            # Update document in database
            document.content = result.content
            document.status = "extracted"
            db.commit()

            print("💾 Document updated in database")
        else:
            print(f"❌ Extraction failed: {result.method}")
            return False

        # Test chunking
        print("\n🔄 Testing document chunking...")
        chunker = DocumentChunker()

        # Reset chunks for testing
        deleted_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).delete()
        db.commit()
        print(f"🗑️ Deleted {deleted_chunks} existing chunks")

        result = await chunker.process_document_from_db(db, document.id)

        if result.success:
            print(f"✅ Chunking successful")
            print(f"📊 Chunks created: {result.chunks_created}")
            print(f"⏱️ Processing time: {result.processing_time:.2f} seconds")

            # Update document status
            document.status = "chunked"
            db.commit()

            print("💾 Document status updated to 'chunked'")
        else:
            print(f"❌ Chunking failed: {result.metadata.get('error', 'Unknown error')}")
            return False

        # Verify chunks were created
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).all()

        print(f"✅ Verification: {len(chunks)} chunks found in database")

        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"  Chunk {i+1}: {len(chunk.chunk_text)} chars, tokens: {chunk.token_count}")

        print("🎉 Pipeline test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)