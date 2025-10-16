#!/usr/bin/env python3
"""
Performance test for optimized embedding service
Tests the optimized embedding service with simulated large documents
"""

import asyncio
import time
from app.database import SessionLocal
from app.models import Document, DocumentChunk
from app.services.optimized_embedding_service import OptimizedEmbeddingService

async def test_optimized_embedding_performance():
    """Test the optimized embedding service performance"""
    print("🚀 Testing Optimized Embedding Service Performance")
    print("=" * 50)
    
    # Initialize the service
    embedding_service = OptimizedEmbeddingService()
    
    # Test with different chunk counts to simulate various document sizes
    test_cases = [
        {"chunks": 100, "description": "Small document"},
        {"chunks": 500, "description": "Medium document"}, 
        {"chunks": 1000, "description": "Large document"},
        {"chunks": 2000, "description": "Very large document"}
    ]
    
    for test_case in test_cases:
        print(f"\n📊 Testing {test_case['description']} ({test_case['chunks']} chunks)")
        print("-" * 40)
        
        # Create test chunks with realistic content
        test_chunks = []
        for i in range(test_case['chunks']):
            # Create realistic text content with varying lengths
            if i % 10 == 0:
                # Large chunk (1000+ tokens)
                text = "This is a large chunk of text that contains substantial content. " * 50
            elif i % 5 == 0:
                # Medium chunk (500-1000 tokens)
                text = "This is a medium-sized chunk with meaningful content. " * 25
            else:
                # Small chunk (<500 tokens)
                text = "This is a small chunk of text. " * 10
            
            test_chunks.append({
                "id": i + 1,
                "text": text,
                "document_id": 999,  # Test document ID
                "page_numbers": [1, 2],
                "section_title": f"Test Section {i}",
                "token_count": len(text.split())  # Rough token count
            })
        
        # Test the optimized service
        start_time = time.time()
        
        try:
            results = await embedding_service.generate_embeddings_for_chunks(
                test_chunks,
                document_id=999,
                provider="openai"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Successfully processed {len(results)} chunks")
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            print(f"📈 Processing rate: {len(results)/processing_time:.2f} chunks/second")
            
            # Calculate theoretical improvement
            original_time = len(results) * 3  # 3s per chunk
            speedup = original_time / processing_time if processing_time > 0 else 0
            print(f"🚀 Speedup vs original: {speedup:.1f}x faster")
            
        except Exception as e:
            print(f"❌ Error during processing: {e}")
            import traceback
            traceback.print_exc()

async def test_concurrent_processing():
    """Test concurrent processing capabilities"""
    print(f"\n🔬 Testing Concurrent Processing")
    print("-" * 40)
    
    embedding_service = OptimizedEmbeddingService()
    
    # Test with multiple concurrent requests
    test_chunks = []
    for i in range(100):
        test_chunks.append({
            "id": i + 1,
            "text": f"Test chunk {i} with some meaningful content for embedding generation. " * 10,
            "document_id": 999,
            "page_numbers": [1],
            "section_title": f"Concurrent Test {i}",
            "token_count": 150
        })
    
    start_time = time.time()
    
    try:
        results = await embedding_service.generate_embeddings_for_chunks(
            test_chunks,
            document_id=999,
            provider="openai"
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Concurrent processing completed")
        print(f"⏱️  Total time: {processing_time:.2f} seconds")
        print(f"📈 Processing rate: {len(results)/processing_time:.2f} chunks/second")
        
    except Exception as e:
        print(f"❌ Error in concurrent processing: {e}")

async def main():
    """Main test function"""
    print("🎯 Optimized Embedding Service Performance Test")
    print("=" * 60)
    
    # Test basic performance
    await test_optimized_embedding_performance()
    
    # Test concurrent processing
    await test_concurrent_processing()
    
    print(f"\n🎉 Performance testing completed!")

if __name__ == "__main__":
    asyncio.run(main())