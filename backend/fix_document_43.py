import os
import sys
import asyncio
from app.database import SessionLocal
from app.models import Document, DocumentChunk, Embedding
from app.services.document_processor import DocumentProcessor
from app.services.document_chunker import DocumentChunker
from app.services.embedding_service import EmbeddingService

async def fix_document_43():
    """Fix document 43 by reprocessing it from extraction to processed"""
    db = SessionLocal()
    
    try:
        print("🔧 Fixing Document 43 processing pipeline...")
        
        # Get document 43
        doc = db.query(Document).filter(Document.id == 43).first()
        if not doc:
            print("❌ Document 43 not found")
            return
        
        print(f"📄 Processing document: {doc.filename}")
        print(f"📊 Current status: {doc.status}")
        print(f"📝 Content length: {len(doc.content) if doc.content else 0}")
        
        # Step 1: Extract content from PNG image
        print("\n🔄 Step 1: Extracting content from PNG image...")
        processor = DocumentProcessor()
        
        if not os.path.exists(doc.file_path):
            print(f"❌ File not found: {doc.file_path}")
            return
        
        # Extract content using Mistral OCR (better for images)
        print("🖼️ Using Mistral OCR for image extraction...")
        result = await processor.extract_with_mistral_ocr(doc.file_path)
        
        if result.success:
            print(f"✅ Extraction successful! Content length: {len(result.content)}")
            
            # Update document with extracted content
            doc.content = result.content
            doc.status = "extracted"
            db.commit()
            print("📝 Document status updated to 'extracted'")
        else:
            print(f"❌ Extraction failed: {result.method}")
            return
        
        # Step 2: Chunk the extracted content
        print("\n🔄 Step 2: Chunking extracted content...")
        chunker = DocumentChunker()
        
        # Delete any existing chunks (clean slate)
        existing_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == 43).delete()
        if existing_chunks > 0:
            print(f"🗑️ Deleted {existing_chunks} existing chunks")
        
        db.commit()
        
        # Chunk the document content
        chunking_result = await chunker.process_document_from_db(db, 43)
        
        if chunking_result.success:
            print(f"✅ Chunking successful! Created {chunking_result.chunks_created} chunks")
            print(f"📊 Chunking metadata: {chunking_result.metadata}")
        else:
            print(f"❌ Chunking failed: {chunking_result.metadata.get('error', 'Unknown error')}")
            return
        
        # Step 3: Generate embeddings
        print("\n🔄 Step 3: Generating embeddings...")
        embedding_service = EmbeddingService(provider="openai")
        
        # Delete any existing embeddings (clean slate)
        # Get chunk IDs first using subquery
        chunk_ids = db.query(DocumentChunk.id).filter(
            DocumentChunk.document_id == 43
        ).subquery()
        
        # Delete embeddings using subquery (safer than join-based delete)
        existing_embeddings = db.query(Embedding).filter(
            Embedding.chunk_id.in_(chunk_ids)
        ).delete(synchronize_session=False)
        
        if existing_embeddings > 0:
            print(f"🗑️ Deleted {existing_embeddings} existing embeddings")
        
        db.commit()
        
        # Generate embeddings for this document
        embedding_result = await embedding_service.process_embeddings_for_document(db, 43)
        
        if embedding_result.success:
            print(f"✅ Embedding generation successful! Created {embedding_result.embeddings_created} embeddings")
            print(f"📊 Embedding metadata: {embedding_result.metadata}")
            
            # Update final status
            doc.status = "processed"
            db.commit()
            print("🎉 Document processing completed successfully!")
        else:
            print(f"❌ Embedding generation failed: {embedding_result.metadata.get('error', 'Unknown error')}")
        
        # Final verification
        print("\n📋 Final verification:")
        chunks_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == 43).count()
        embeddings_count = db.query(Embedding).join(DocumentChunk).filter(
            DocumentChunk.document_id == 43
        ).count()
        
        print(f"📄 Document status: {doc.status}")
        print(f"📝 Content length: {len(doc.content) if doc.content else 0}")
        print(f"🧩 Chunks created: {chunks_count}")
        print(f"🔢 Embeddings created: {embeddings_count}")
        
    except Exception as e:
        print(f"❌ Error fixing document 43: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(fix_document_43())