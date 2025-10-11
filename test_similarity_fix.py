#!/usr/bin/env python3
"""
Test script to verify the similarity search fix in chat.py
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models import Document, DocumentChunk, Embedding
from app.routers.chat import get_context_from_db, cosine_similarity

async def test_similarity_search():
    """Test the fixed similarity search functionality"""
    print("Testing similarity search fix...")

    # Test the cosine similarity function
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    vec3 = [1.0, 0.0, 0.0]

    similarity_1_2 = cosine_similarity(vec1, vec2)
    similarity_1_3 = cosine_similarity(vec1, vec3)

    print(f"Similarity between different vectors: {similarity_1_2:.4f}")
    print(f"Similarity between identical vectors: {similarity_1_3:.4f}")

    # Check database for documents with embeddings
    db = SessionLocal()

    try:
        # Look for documents with embeddings
        docs_with_embeddings = db.query(Document).join(
            DocumentChunk, Document.id == DocumentChunk.document_id
        ).join(
            Embedding, DocumentChunk.id == Embedding.chunk_id
        ).filter(
            Embedding.embedding_vector.isnot(None)
        ).distinct().all()

        print(f"\nFound {len(docs_with_embeddings)} documents with embeddings")

        if docs_with_embeddings:
            # Test with the first document
            test_doc = docs_with_embeddings[0]
            print(f"Testing with document: {test_doc.filename}")

            # Test query
            test_query = "What is this document about?"
            print(f"Query: {test_query}")

            # Get context using the fixed function
            context, references = await get_context_from_db(test_query, db, test_doc.id)

            if context:
                print(f"\n✅ SUCCESS: Found relevant context!")
                print(f"Context length: {len(context)} characters")
                print(f"Number of references: {len(references)}")
                print("\nFirst 200 characters of context:")
                print(context[:200] + "...")
            else:
                print("\n❌ No context found - similarity search may still have issues")

        else:
            print("\n❌ No documents with embeddings found")
            print("Need to process documents first")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_similarity_search())