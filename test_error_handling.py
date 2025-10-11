#!/usr/bin/env python3
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend URL
BACKEND_URL = "http://localhost:8000"

def test_login():
    """Test login functionality"""
    login_url = f"{BACKEND_URL}/api/auth/login"

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
            token = data.get('access_token')
            print(f"Token: {token[:50]}...")
            return token
        else:
            print(f"ERROR: Login failed - {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: Request failed - {e}")
        return None

def upload_unsupported_file(token):
    """Upload a file with unsupported extension"""
    if not token:
        print("No token available for upload")
        return None

    upload_url = f"{BACKEND_URL}/api/documents/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Upload the unsupported file
    test_file_path = "test_unsupported.txt"

    if not os.path.exists(test_file_path):
        print(f"ERROR: Test file not found: {test_file_path}")
        return None

    print(f"Uploading unsupported file: {test_file_path}")

    try:
        with open(test_file_path, 'rb') as f:
            files = {"file": ("test_unsupported.txt", f, "text/plain")}
            response = requests.post(upload_url, files=files, headers=headers)

        print(f"Upload Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Unsupported file uploaded successfully!")
            document_id = data.get('document', {}).get('id')
            print(f"Document ID: {document_id}")
            return document_id
        else:
            print(f"ERROR: Upload failed - {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: Upload request failed - {e}")
        return None

def test_unsupported_extraction(token, document_id):
    """Test extraction of unsupported file format"""
    if not token:
        print("No token available for extraction test")
        return False

    extract_url = f"{BACKEND_URL}/api/documents/{document_id}/extract"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"Testing extraction for unsupported file format (document ID: {document_id})")

    try:
        response = requests.post(extract_url, headers=headers)
        print(f"Extraction Status Code: {response.status_code}")

        if response.status_code == 500:
            data = response.json()
            print("SUCCESS: Unsupported file format properly rejected!")
            print(f"Error message: {data.get('detail', 'Unknown error')}")
            return True
        else:
            print(f"ERROR: Expected 500 status code for unsupported format, got {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: Extraction request failed - {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Error Handling for Unsupported File Formats ===")

    # Test login
    token = test_login()

    if token:
        print("\n=== Uploading Unsupported File ===")

        # Upload unsupported file
        document_id = upload_unsupported_file(token)

        if document_id:
            print("\n=== Testing Error Handling ===")

            # Test error handling
            error_handling_works = test_unsupported_extraction(token, document_id)

            if error_handling_works:
                print("\nSUCCESS: Error handling for unsupported file formats is working correctly!")
                print("The system properly rejects unsupported file types with appropriate error messages.")
                sys.exit(0)
            else:
                print(f"\nERROR: Error handling test failed for document {document_id}")
                sys.exit(1)
        else:
            print("\nERROR: Could not upload test file")
            sys.exit(1)
    else:
        print("\nERROR: Authentication failed. Cannot test error handling.")
        sys.exit(1)