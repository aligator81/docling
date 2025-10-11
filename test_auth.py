#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend URL
BACKEND_URL = "http://localhost:8000"

def test_login():
    """Test login functionality"""
    login_url = f"{BACKEND_URL}/api/auth/login"

    # Test data
    credentials = {
        "username": "testuser",
        "password": "testpassword123"
    }

    print(f"Testing login with: {credentials['username']}")

    try:
        response = requests.post(login_url, data=credentials)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Login successful!")
            print(f"Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"User: {data.get('user', {}).get('username', 'N/A')}")
            return data.get('access_token')
        else:
            print(f"ERROR: Login failed - {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: Request failed - {e}")
        return None

def test_chat_with_token(token):
    """Test chat functionality with authentication token"""
    if not token:
        print("No token available for chat test")
        return False

    chat_url = f"{BACKEND_URL}/api/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    chat_data = {
        "message": "Hello, can you help me with a test?"
    }

    print("Testing chat with authentication...")

    try:
        response = requests.post(chat_url, json=chat_data, headers=headers)
        print(f"Chat Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Chat response received!")
            print(f"Response: {data.get('response', 'N/A')[:100]}...")
            return True
        else:
            print(f"ERROR: Chat failed - {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: Chat request failed - {e}")
        return False

def test_chat_history(token):
    """Test chat history endpoint"""
    if not token:
        print("No token available for history test")
        return False

    history_url = f"{BACKEND_URL}/api/chat/history?limit=10"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("Testing chat history...")

    try:
        response = requests.get(history_url, headers=headers)
        print(f"History Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Retrieved {len(data)} chat history records")
            return True
        else:
            print(f"ERROR: History failed - {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: History request failed - {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Authentication and Chat ===")

    # Test login
    token = test_login()

    if token:
        print("\n=== Testing Chat Functionality ===")

        # Test chat
        chat_success = test_chat_with_token(token)

        # Test chat history
        history_success = test_chat_history(token)

        if chat_success and history_success:
            print("\nSUCCESS: All tests passed! Chat functionality is working correctly.")
        else:
            print("\nERROR: Some tests failed. Check the errors above.")
    else:
        print("\nERROR: Authentication failed. Cannot test chat functionality.")