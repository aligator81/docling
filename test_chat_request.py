#!/usr/bin/env python3
"""
Test script to simulate the actual chat request and see what error occurs
"""

import requests
import json
import os

def test_chat_request():
    """Test the actual chat API endpoint"""
    
    # Get the token from environment or use a test token
    token = os.getenv("TEST_TOKEN")
    if not token:
        print("❌ No token available. Please set TEST_TOKEN environment variable.")
        print("   You can get a token by logging in via the frontend and checking localStorage")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test data - using document 43 which should be ready
    test_data = {
        "message": "What is this document about?",
        "document_ids": [43]
    }
    
    url = "http://localhost:8000/api/chat"
    
    try:
        print("🔍 Testing chat API endpoint...")
        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=test_data, timeout=30)
        
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
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
    test_chat_request()