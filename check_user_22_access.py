#!/usr/bin/env python3
"""
Check if user ID 22 still exists and can access documents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models import User, Document

def check_user_22_access():
    """Check if user ID 22 exists and can access documents"""
    db = SessionLocal()
    
    try:
        print("🔍 Checking user ID 22 access...")
        
        # Check if user 22 exists
        user_22 = db.query(User).filter(User.id == 22).first()
        if not user_22:
            print("❌ User ID 22 does not exist")
            return
        
        print(f"✅ User ID 22 exists:")
        print(f"   Username: {user_22.username}")
        print(f"   Role: {user_22.role}")
        print(f"   Is Active: {user_22.is_active}")
        
        # Check what documents user 22 owns
        user_documents = db.query(Document).filter(Document.user_id == 22).all()
        print(f"\n📋 Documents owned by user 22: {len(user_documents)}")
        
        for doc in user_documents:
            print(f"   - ID: {doc.id}, Name: {doc.original_filename}, Status: {doc.status}")
        
        # Check if user 22 can access document 43 (which is now owned by admin)
        doc_43 = db.query(Document).filter(Document.id == 43).first()
        if doc_43:
            print(f"\n📄 Document 43 details:")
            print(f"   Name: {doc_43.original_filename}")
            print(f"   Owner: User ID {doc_43.user_id}")
            print(f"   Status: {doc_43.status}")
            
            if doc_43.user_id == 22:
                print("   ✅ User 22 OWNS this document")
            else:
                print(f"   ❌ User 22 does NOT own this document (owned by user {doc_43.user_id})")
                
        # Check if there are any other users
        all_users = db.query(User).all()
        print(f"\n👥 All users in system: {len(all_users)}")
        for user in all_users:
            print(f"   - ID: {user.id}, Username: {user.username}, Role: {user.role}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user_22_access()