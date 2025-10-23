#!/usr/bin/env python3
"""
Test chat with authentication to see the actual API key issue
"""

import requests
import json
import os

def get_auth_token():
    """Get authentication token by logging in"""
    login_data = {
        "username": "admin",
        "password": "admin123"  # Default admin password
    }
    
    url = "http://localhost:8000/api/auth/login"
    
    try:
        response = requests.post(url, data=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_chat_with_auth():
    """Test chat endpoint with authentication"""
    
    token = get_auth_token()
    if not token:
        print("❌ Could not get authentication token")
        return
    
    print(f"✅ Got authentication token: {token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test data
    test_data = {
        "message": "hi",
        "document_ids": [60]
    }
    
    url = "http://localhost:8000/api/chat"
    
    try:
        print("🔍 Testing chat endpoint with authentication...")
        response = requests.post(url, headers=headers, json=test_data, timeout=30)
        
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
    test_chat_with_auth()