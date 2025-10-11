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

def upload_test_document(token):
    """Upload a test document"""
    if not token:
        print("No token available for upload")
        return None

    upload_url = f"{BACKEND_URL}/api/documents/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Upload the test document
    test_file_path = "test_document.md"

    if not os.path.exists(test_file_path):
        print(f"ERROR: Test file not found: {test_file_path}")
        return None

    print(f"Uploading test document: {test_file_path}")

    try:
        with open(test_file_path, 'rb') as f:
            files = {"file": ("test_document.md", f, "text/markdown")}
            response = requests.post(upload_url, files=files, headers=headers)

        print(f"Upload Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Document uploaded successfully!")
            document_id = data.get('document', {}).get('id')
            print(f"Document ID: {document_id}")
            return document_id
        else:
            print(f"ERROR: Upload failed - {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: Upload request failed - {e}")
        return None

def test_document_extraction(token, document_id):
    """Test document extraction functionality"""
    if not token:
        print("No token available for extraction test")
        return False

    extract_url = f"{BACKEND_URL}/api/documents/{document_id}/extract"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"Testing document extraction for document ID: {document_id}")

    try:
        response = requests.post(extract_url, headers=headers)
        print(f"Extraction Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Document extraction completed!")
            print(f"Method: {data.get('extraction_method')}")
            print(f"Processing time: {data.get('processing_time'):.2f}s")
            print(f"Content length: {data.get('content_length')} characters")
            return True
        else:
            print(f"ERROR: Document extraction failed - {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: Extraction request failed - {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Document Upload and Extraction ===")

    # Test login
    token = test_login()

    if token:
        print("\n=== Uploading Test Document ===")

        # Upload test document
        document_id = upload_test_document(token)

        if document_id:
            print("\n=== Testing Extraction ===")

            # Test extraction
            extraction_success = test_document_extraction(token, document_id)

            if extraction_success:
                print("\nSUCCESS: Document extraction is working correctly!")
                print("The fix for the Docling configuration issue is successful!")
                sys.exit(0)
            else:
                print(f"\nERROR: Document extraction failed for document {document_id}")
                sys.exit(1)
        else:
            print("\nERROR: Could not upload test document")
            sys.exit(1)
    else:
        print("\nERROR: Authentication failed. Cannot test document extraction.")
        sys.exit(1)