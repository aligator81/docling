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

def test_upload_file(token, file_path):
    """Test file upload functionality with authentication token"""
    if not token:
        print("No token available for upload test")
        return False

    if not os.path.exists(file_path):
        print(f"ERROR: File {file_path} does not exist")
        return False

    upload_url = f"{BACKEND_URL}/api/documents/upload"
    headers = {
        "Authorization": f"Bearer {token}",
    }

    print(f"Testing file upload: {file_path}")

    try:
        with open(file_path, 'rb') as file:
            files = {"file": (os.path.basename(file_path), file, "application/markdown")}
            response = requests.post(upload_url, files=files, headers=headers)

        print(f"Upload Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: File uploaded successfully!")
            print(f"Document ID: {data.get('document', {}).get('id', 'N/A')}")
            print(f"Original filename: {data.get('document', {}).get('original_filename', 'N/A')}")
            return True
        else:
            print(f"ERROR: Upload failed - {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: Upload request failed - {e}")
        return False

def test_list_documents(token):
    """Test listing documents"""
    if not token:
        print("No token available for document listing test")
        return False

    list_url = f"{BACKEND_URL}/api/documents"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("Testing document listing...")

    try:
        response = requests.get(list_url, headers=headers)
        print(f"List Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Retrieved {len(data)} documents")
            for doc in data:
                print(f"  - {doc.get('original_filename')} (ID: {doc.get('id')})")
            return True
        else:
            print(f"ERROR: List failed - {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: List request failed - {e}")
        return False

if __name__ == "__main__":
    print("=== Testing File Upload Functionality ===")

    # Test login first
    token = test_login()

    if token:
        print("\n=== Testing File Upload ===")

        # Test uploading plan.md
        file_path = "plan.md"
        upload_success = test_upload_file(token, file_path)

        if upload_success:
            print("\n=== Testing Document Listing ===")
            list_success = test_list_documents(token)

            if list_success:
                print("\nSUCCESS: All upload tests passed!")
            else:
                print("\nERROR: Document listing failed after successful upload")
        else:
            print("\nERROR: File upload failed")
    else:
        print("\nERROR: Authentication failed. Cannot test upload functionality.")