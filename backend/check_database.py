from app.database import SessionLocal
from app.models import Document, DocumentChunk, Embedding

def check_document_state():
    db = SessionLocal()
    try:
        # List all documents
        docs = db.query(Document).all()
        print(f'Total documents: {len(docs)}')
        for doc in docs:
            print(f'ID: {doc.id}, Filename: {doc.original_filename}, Status: {doc.status}')

        # If there are documents, check the first one
        if docs:
            doc = docs[0]
            print(f'\nChecking first document {doc.id}:')
            print(f'Status: {doc.status}')
            print(f'Content length: {len(doc.content) if doc and doc.content else 0}')

            # Check chunks
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
            print(f'Chunks found: {len(chunks)}')

            # Check embeddings
            embeddings = db.query(Embedding).join(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
            print(f'Embeddings found: {len(embeddings)}')

            # Print first few chunks for debugging
            if chunks:
                print("\nFirst 3 chunks preview:")
                for i, chunk in enumerate(chunks[:3]):
                    print(f"Chunk {i}: {chunk.chunk_text[:100]}...")

    finally:
        db.close()

if __name__ == "__main__":
    check_document_state()