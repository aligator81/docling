#!/usr/bin/env python3
"""
Final test to verify frontend chat functionality works correctly
"""

import requests
import json

def test_complete_chat_flow():
    """Test the complete chat flow with authentication and document selection"""
    
    # Step 1: Login to get token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    login_url = "http://localhost:8000/api/auth/login"
    
    try:
        print("🔐 Step 1: Authenticating...")
        login_response = requests.post(login_url, data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        login_data = login_response.json()
        token = login_data.get("access_token")
        user = login_data.get("user")
        
        print(f"✅ Logged in as: {user.get('username')} (ID: {user.get('id')})")
        print(f"   Token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Get available documents
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    documents_url = "http://localhost:8000/api/documents"
    
    try:
        print("\n📋 Step 2: Getting available documents...")
        documents_response = requests.get(documents_url, headers=headers)
        
        if documents_response.status_code != 200:
            print(f"❌ Failed to get documents: {documents_response.status_code}")
            print(f"Response: {documents_response.text}")
            return
        
        documents = documents_response.json()
        print(f"✅ Found {len(documents)} documents")
        
        for doc in documents:
            print(f"   - ID: {doc['id']}, Name: {doc['original_filename']}, Status: {doc['status']}")
            
    except Exception as e:
        print(f"❌ Documents error: {e}")
        return
    
    # Step 3: Test chat with document 43
    chat_url = "http://localhost:8000/api/chat"
    chat_data = {
        "message": "What is this document about?",
        "document_ids": [43]  # Use the fixed document
    }
    
    try:
        print(f"\n💬 Step 3: Testing chat with document 43...")
        chat_response = requests.post(chat_url, headers=headers, json=chat_data, timeout=30)
        
        print(f"📡 Chat Response Status: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            print("✅ Chat request SUCCESSFUL!")
            result = chat_response.json()
            print(f"🤖 AI Response: {result['response']}")
            print(f"📊 Model used: {result['model_used']}")
            print(f"📄 Context documents: {result['context_docs']}")
        else:
            print("❌ Chat request FAILED!")
            try:
                error_data = chat_response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {chat_response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_complete_chat_flow()