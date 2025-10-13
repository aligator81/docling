from app.database import SessionLocal
from app.models import Document, DocumentChunk, Embedding

def check_document_state():
    db = SessionLocal()
    try:
        # Check document 43
        doc = db.query(Document).filter(Document.id == 43).first()
        print(f'Document 43: {doc.filename if doc else "Not found"}')
        print(f'Status: {doc.status if doc else "N/A"}')
        print(f'Content length: {len(doc.content) if doc and doc.content else 0}')
        
        # Check chunks for document 43
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == 43).all()
        print(f'Chunks found: {len(chunks)}')
        
        # Check embeddings for document 43
        embeddings = db.query(Embedding).join(DocumentChunk).filter(DocumentChunk.document_id == 43).all()
        print(f'Embeddings found: {len(embeddings)}')
        
        # Check if any chunks exist without embeddings
        chunks_without_embeddings = db.query(DocumentChunk).outerjoin(
            Embedding, DocumentChunk.id == Embedding.chunk_id
        ).filter(
            DocumentChunk.document_id == 43,
            Embedding.id.is_(None)
        ).all()
        print(f'Chunks without embeddings: {len(chunks_without_embeddings)}')
        
        # Print first few chunks for debugging
        if chunks:
            print("\nFirst 3 chunks preview:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"Chunk {i}: {chunk.chunk_text[:100]}...")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_document_state()