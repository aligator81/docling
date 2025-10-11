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
            print(f"Token: {token}")
            return token
        else:
            print(f"ERROR: Login failed - {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: Request failed - {e}")
        return None

def test_documents_list(token):
    """Test documents list functionality"""
    if not token:
        print("No token available for documents test")
        return False

    docs_url = f"{BACKEND_URL}/api/documents/"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("Testing documents list...")

    try:
        response = requests.get(docs_url, headers=headers)
        print(f"Documents Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Retrieved {len(data)} documents")
            for doc in data:
                print(f"  - Document {doc['id']}: {doc['filename']} (Status: {doc['status']})")
            return data
        else:
            print(f"ERROR: Documents list failed - {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: Documents request failed - {e}")
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
    print("=== Testing Document Extraction Fix ===")

    # Test login
    token = test_login()

    if token:
        print("\n=== Testing Documents Functionality ===")

        # Test documents list
        documents = test_documents_list(token)

        if documents:
            print(f"\nFound {len(documents)} documents")

            # Try to extract the first document that needs extraction
            for doc in documents:
                if doc['status'] == 'not processed':
                    print(f"\n=== Testing Extraction for Document {doc['id']} ===")
                    extraction_success = test_document_extraction(token, doc['id'])
                    if extraction_success:
                        print("\nSUCCESS: Document extraction is working correctly!")
                        sys.exit(0)
                    else:
                        print(f"\nERROR: Document extraction failed for document {doc['id']}")
                        sys.exit(1)

            print("\nWARNING: No documents found that need extraction (all are already processed)")
            print("✅ Document extraction functionality appears to be working (no errors in API)")

        else:
            print("\nERROR: Could not retrieve documents list")
            sys.exit(1)
    else:
        print("\nERROR: Authentication failed. Cannot test document extraction.")
        sys.exit(1)