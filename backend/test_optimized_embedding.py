"""
Test script for Optimized Embedding Service

This script tests the optimized embedding service with all performance improvements:
- Batch processing (30 chunks per batch)
- Concurrent processing (8 concurrent batches) 
- Reduced rate limiting (0.5s instead of 3s)
- Database batch commits
"""

import asyncio
import time
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services.optimized_embedding_service import OptimizedEmbeddingService
from app.models import Document, DocumentChunk, Embedding

async def test_optimized_embedding_service():
    """Test the optimized embedding service"""
    print("🧪 Testing Optimized Embedding Service")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Initialize the optimized service
        print("🚀 Initializing OptimizedEmbeddingService...")
        service = OptimizedEmbeddingService(provider="openai")
        
        # Test configuration
        print(f"📊 Service Configuration:")
        print(f"  • Batch size: {service.batch_size} chunks per batch")
        print(f"  • Concurrent batches: {service.max_concurrent_batches}")
        print(f"  • Rate limit delay: {service.rate_limit_delay}s (reduced from 3s)")
        print(f"  • Max retries: {service.max_retries}")
        
        # Get stats before processing
        print("\n📈 Pre-processing Statistics:")
        stats_before = service.get_embedding_stats(db)
        print(f"  • Total embeddings: {stats_before.get('total_embeddings', 0)}")
        
        # Find chunks that need embeddings
        chunks_needing_embeddings = db.query(DocumentChunk).join(
            Document, DocumentChunk.document_id == Document.id
        ).outerjoin(
            Embedding, DocumentChunk.id == Embedding.chunk_id
        ).filter(
            Embedding.id.is_(None)  # No embedding exists
        ).count()
        
        print(f"  • Chunks needing embeddings: {chunks_needing_embeddings}")
        
        if chunks_needing_embeddings == 0:
            print("⚠️ No chunks found that need embeddings. Creating test chunks...")
            # Create some test chunks if none exist
            test_doc = db.query(Document).first()
            if test_doc:
                test_chunks = [
                    DocumentChunk(
                        document_id=test_doc.id,
                        chunk_text=f"Test chunk {i} for optimized embedding service testing.",
                        chunk_index=i,
                        page_numbers=[1],
                        section_title=f"Test Section {i}",
                        chunk_type="paragraph",
                        token_count=10
                    ) for i in range(5)
                ]
                db.add_all(test_chunks)
                db.commit()
                print("✅ Created 5 test chunks")
        
        # Test the optimized processing
        print("\n🧪 Testing Optimized Processing...")
        start_time = time.time()
        
        result = await service.process_embeddings_from_db(db, resume=False)
        
        processing_time = time.time() - start_time
        
        print(f"\n📊 Test Results:")
        print(f"  • Success: {result.success}")
        print(f"  • Embeddings created: {result.embeddings_created}")
        print(f"  • Processing time: {processing_time:.2f} seconds")
        print(f"  • Rate: {result.embeddings_created/processing_time:.2f} chunks/second")
        
        if result.metadata:
            print(f"  • Failed embeddings: {result.metadata.get('failed_embeddings', 0)}")
            print(f"  • Final embedding count: {result.metadata.get('final_embedding_count', 0)}")
        
        # Get stats after processing
        print("\n📈 Post-processing Statistics:")
        stats_after = service.get_embedding_stats(db)
        print(f"  • Total embeddings: {stats_after.get('total_embeddings', 0)}")
        
        # Performance comparison
        if chunks_needing_embeddings > 0:
            original_estimated_time = chunks_needing_embeddings * 3  # 3s per chunk
            optimized_time = processing_time
            speedup = original_estimated_time / optimized_time if optimized_time > 0 else 0
            
            print(f"\n🚀 Performance Comparison:")
            print(f"  • Original estimated time: {original_estimated_time:.2f}s")
            print(f"  • Optimized actual time: {optimized_time:.2f}s")
            print(f"  • Speedup: {speedup:.1f}x faster")
        
        # Cleanup
        service.cleanup_checkpoint()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

async def test_batch_processing():
    """Test batch processing functionality specifically"""
    print("\n🧪 Testing Batch Processing...")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        service = OptimizedEmbeddingService(provider="openai")
        
        # Create test batch data
        test_texts = [
            f"Test text for batch processing {i}. This is a sample text for embedding generation."
            for i in range(10)
        ]
        
        print(f"🔄 Testing batch embedding generation for {len(test_texts)} texts...")
        start_time = time.time()
        
        embeddings = await service.get_batch_embeddings(test_texts)
        
        batch_time = time.time() - start_time
        
        print(f"✅ Batch processing completed:")
        print(f"  • Texts processed: {len(test_texts)}")
        print(f"  • Embeddings generated: {len(embeddings)}")
        print(f"  • Batch processing time: {batch_time:.2f}s")
        print(f"  • Rate: {len(test_texts)/batch_time:.2f} texts/second")
        
        # Verify embeddings
        if embeddings:
            print(f"  • Embedding dimensions: {len(embeddings[0])}")
            print(f"  • All embeddings have same dimensions: {all(len(e) == len(embeddings[0]) for e in embeddings)}")
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Optimized Embedding Service Test Suite")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_optimized_embedding_service())
    asyncio.run(test_batch_processing())
    
    print("\n🎉 All tests completed!")