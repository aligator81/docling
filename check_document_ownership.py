#!/usr/bin/env python3
"""
Check document ownership and fix permission issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models import Document, User

def check_and_fix_document_ownership():
    """Check document ownership and fix if needed"""
    db = SessionLocal()
    
    try:
        print("🔍 Checking document ownership...")
        
        # Get all documents
        documents = db.query(Document).all()
        print(f"📋 Total documents: {len(documents)}")
        
        # Get admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("❌ Admin user not found")
            return
        
        print(f"👤 Admin user ID: {admin_user.id}")
        
        for doc in documents:
            print(f"\n📄 Document ID: {doc.id}")
            print(f"   Filename: {doc.original_filename}")
            print(f"   Current user_id: {doc.user_id}")
            print(f"   Status: {doc.status}")
            
            # Check if admin owns this document
            if doc.user_id != admin_user.id:
                print(f"   ❌ Admin does NOT own this document")
                
                # Fix ownership
                old_user_id = doc.user_id
                doc.user_id = admin_user.id
                db.commit()
                print(f"   ✅ Fixed ownership: {old_user_id} → {admin_user.id}")
            else:
                print(f"   ✅ Admin owns this document")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_document_ownership()