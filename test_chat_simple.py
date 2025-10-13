#!/usr/bin/env python3
"""
Simple test to trigger a chat request and see the actual error
"""

import requests
import json

def test_chat():
    """Test chat endpoint with document 43"""
    
    # Test data
    test_data = {
        "message": "What is this document about?",
        "document_ids": [43]
    }
    
    url = "http://localhost:8000/api/chat"
    
    try:
        print("🔍 Testing chat endpoint...")
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Chat request SUCCESSFUL!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print("❌ Chat request FAILED!")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_chat()