#!/usr/bin/env python3
"""
Debug script to identify why documents show as 'not available' in chat
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models import Document, DocumentChunk, Embedding
from backend.app.auth import get_current_active_user
from backend.app.routers.chat import get_context_from_db
import asyncio

async def debug_chat_issue():
    """Debug the chat document availability issue"""
    db = SessionLocal()
    
    try:
        print("🔍 DEBUGGING CHAT DOCUMENT AVAILABILITY ISSUE")
        print("=" * 60)
        
        # Get all documents
        documents = db.query(Document).all()
        print(f"📋 Total documents in database: {len(documents)}")
        
        for doc in documents:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Filename: {doc.original_filename}")
            print(f"   Status: {doc.status}")
            print(f"   User ID: {doc.user_id}")
            
            # Check chunks
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
            print(f"   Chunks: {len(chunks)}")
            
            # Check embeddings
            embeddings_count = 0
            for chunk in chunks:
                embedding = db.query(Embedding).filter(Embedding.chunk_id == chunk.id).first()
                if embedding:
                    embeddings_count += 1
            
            print(f"   Embeddings: {embeddings_count}")
            
            # Check if document is ready for chat
            is_ready = (doc.status == "processed" and
                       len(chunks) > 0 and
                       embeddings_count == len(chunks))
            
            print(f"   Ready for chat: {'✅ YES' if is_ready else '❌ NO'}")
        
        print("\n" + "=" * 60)
        print("🧪 TESTING CHAT CONTEXT RETRIEVAL")
        
        # Test with document 43 (which should be ready)
        test_doc_id = 43
        test_query = "What is this document about?"
        
        print(f"\nTesting chat with document {test_doc_id}...")
        context, references = await get_context_from_db(test_query, db, [test_doc_id], None)
        
        print(f"Context retrieved: {'✅ YES' if context else '❌ NO'}")
        print(f"Context length: {len(context)}")
        print(f"References found: {len(references)}")
        
        if references:
            for ref in references:
                print(f"  - {ref.get('filename', 'Unknown')} (similarity: {ref.get('similarity', 0):.3f})")
        
        print("\n" + "=" * 60)
        print("🔍 CHECKING CHAT ROUTER LOGIC")
        
        # Simulate the chat router document validation
        from backend.app.routers.chat import router
        from backend.app.schemas import ChatMessage
        
        print(f"\nSimulating chat router document validation...")
        
        # Test with valid document
        try:
            message = ChatMessage(message=test_query, document_ids=[test_doc_id])
            print(f"✅ Document {test_doc_id} validation: PASS")
        except Exception as e:
            print(f"❌ Document {test_doc_id} validation: FAIL - {e}")
        
        # Test with invalid document
        try:
            message = ChatMessage(message=test_query, document_ids=[999])
            print(f"❌ Invalid document validation: UNEXPECTEDLY PASSED")
        except Exception as e:
            print(f"✅ Invalid document validation: CORRECTLY FAILED - {e}")
            
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_chat_issue())