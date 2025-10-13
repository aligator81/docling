#!/usr/bin/env python3
"""
Script to update document status from 'embedding' to 'processed'
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Document

def update_document_status():
    """Update all documents with status 'embedding' to 'processed'"""
    db = SessionLocal()
    
    try:
        # Find documents with 'embedding' status
        documents_to_update = db.query(Document).filter(Document.status == 'embedding').all()
        
        if not documents_to_update:
            print("✅ No documents found with 'embedding' status")
            return
        
        print(f"🔍 Found {len(documents_to_update)} document(s) with 'embedding' status")
        
        # Update each document
        for doc in documents_to_update:
            print(f"🔄 Updating document ID {doc.id}: '{doc.filename}' from 'embedding' to 'processed'")
            doc.status = 'processed'
        
        # Commit the changes
        db.commit()
        print(f"✅ Successfully updated {len(documents_to_update)} document(s) to 'processed' status")
        
    except Exception as e:
        print(f"❌ Error updating document status: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting document status update...")
    update_document_status()
    print("🎉 Document status update completed!")