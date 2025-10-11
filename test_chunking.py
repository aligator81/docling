import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.document_chunker import DocumentChunker
from app.database import SessionLocal

async def test_chunking():
    print("🔄 Testing chunking functionality...")
    chunker = DocumentChunker()
    db = SessionLocal()

    try:
        result = await chunker.process_all_documents_from_db(db)
        print(f"✅ Chunking completed. Processed {result} documents.")
    except Exception as e:
        print(f"❌ Error during chunking: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_chunking())