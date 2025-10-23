#!/usr/bin/env python3
"""
Test script to verify the chat embedding fix
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = "/api/auth/login"
CHAT_ENDPOINT = "/api/chat"

def test_chat_without_document_ids():
    """Test chat without specifying document IDs - should search all available documents"""
    
    print("🔍 Testing chat endpoint without document IDs...")
    
    # Login first - use form data for OAuth2
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # Login to get token - use form data instead of JSON
        response = requests.post(f"{BASE_URL}{LOGIN_ENDPOINT}", data=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        token = response.json().get("access_token")
        if not token:
            print("❌ No access token received")
            return False
            
        print(f"✅ Got authentication token")
        
        # Test chat without document IDs
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "message": "What is this document about?",
            "document_ids": []  # Empty list to search all documents
        }
        
        print(f"📡 Sending chat request: {chat_data['message']}")
        response = requests.post(f"{BASE_URL}{CHAT_ENDPOINT}", json=chat_data, headers=headers)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Chat request SUCCESS!")
            print(f"🤖 Response: {result.get('response', 'No response')}")
            print(f"📚 Context docs: {result.get('context_docs', [])}")
            references = result.get('references', []) or []
            print(f"🔗 References: {len(references)}")
            print(f"🤖 Model used: {result.get('model_used', 'Unknown')}")
            return True
        else:
            print(f"❌ Chat request FAILED!")
            print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing chat embedding fix...")
    success = test_chat_without_document_ids()
    
    if success:
        print("\n🎉 Chat embedding fix appears to be working!")
        print("✅ No more dimension mismatch errors")
    else:
        print("\n❌ Chat embedding fix may still have issues")
        sys.exit(1)