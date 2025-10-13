#!/usr/bin/env python3
"""
Test script to verify if user ID 22 (superadmin) can chat with document 43
"""

import sys
import os
import requests
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.app.database import SessionLocal
from backend.app.models import User, Document

def test_user_22_chat_access():
    """Test if user 22 can access document 43 for chat"""
    
    print("🔍 Testing User 22 Chat Access to Document 43")
    print("=" * 50)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get user 22 details
        user_22 = db.query(User).filter(User.id == 22).first()
        if not user_22:
            print("❌ User ID 22 not found")
            return
        
        print(f"✅ User 22: {user_22.username} (Role: {user_22.role})")
        
        # Get document 43 details
        doc_43 = db.query(Document).filter(Document.id == 43).first()
        if not doc_43:
            print("❌ Document 43 not found")
            return
        
        print(f"📄 Document 43: {doc_43.original_filename} (Owner: User {doc_43.user_id}, Status: {doc_43.status})")
        
        # Check if user 22 can access document 43 based on chat router logic
        if user_22.role in ["admin", "super_admin"]:
            print("✅ User 22 has admin/super_admin role - should be able to access ANY document")
            document = db.query(Document).filter(Document.id == 43).first()
            if document:
                print("✅ Document 43 found for user 22 (admin access)")
            else:
                print("❌ Document 43 not found (this shouldn't happen)")
        else:
            print("❌ User 22 is not admin/super_admin - can only access owned documents")
            document = db.query(Document).filter(
                Document.id == 43,
                Document.user_id == 22
            ).first()
            if document:
                print("✅ User 22 owns document 43")
            else:
                print("❌ User 22 does NOT own document 43")
        
        # Test the actual chat endpoint
        print("\n🔗 Testing chat endpoint...")
        
        # You would need to get an auth token for user 22 first
        # For now, let's just check the logic
        
        print("\n📋 Summary:")
        print(f"   - User 22 role: {user_22.role}")
        print(f"   - Document 43 owner: User {doc_43.user_id}")
        print(f"   - Document 43 status: {doc_43.status}")
        print(f"   - Should user 22 be able to chat with doc 43? {'YES' if user_22.role in ['admin', 'super_admin'] else 'NO'}")
        
        if user_22.role in ["admin", "super_admin"]:
            print("✅ User 22 SHOULD be able to chat with document 43 (admin privileges)")
        else:
            print("❌ User 22 CANNOT chat with document 43 (not admin and doesn't own it)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_user_22_chat_access()