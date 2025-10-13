import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_openai_connection():
    """Test OpenAI API connection and embedding generation"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Test a simple embedding request
        test_text = "This is a test document for embedding generation."
        print(f"🔄 Testing embedding generation for: '{test_text}'")
        
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=test_text
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Embedding generated successfully! Dimensions: {len(embedding)}")
        print(f"📊 First 5 values: {embedding[:5]}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

def test_embedding_service():
    """Test the embedding service directly"""
    from app.services.embedding_service import EmbeddingService
    
    try:
        print("\n🧪 Testing EmbeddingService...")
        service = EmbeddingService(provider="openai")
        
        # Test with a simple text
        test_text = "This is a test document for embedding service."
        print(f"🔄 Testing embedding service with: '{test_text}'")
        
        # Test the validate_and_split_chunk method
        chunks, token_counts = service.validate_and_split_chunk(test_text)
        print(f"✅ Chunk validation successful")
        print(f"📊 Chunks: {len(chunks)}, Token counts: {token_counts}")
        
        return True
        
    except Exception as e:
        print(f"❌ EmbeddingService error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing OpenAI API and Embedding Service...")
    print("=" * 50)
    
    # Test OpenAI connection
    openai_success = test_openai_connection()
    
    # Test embedding service
    service_success = test_embedding_service()
    
    print("\n" + "=" * 50)
    if openai_success and service_success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed. Check the errors above.")