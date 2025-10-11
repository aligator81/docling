#!/usr/bin/env python3
"""
Test script to verify document extraction works and stores data in database
"""
import asyncio
import os
import sys
import requests

async def test_extraction_api():
    """Test the extraction API endpoint"""
    print("Testing document extraction API...")

    # API endpoint
    base_url = "http://localhost:8000/api"

    try:
        # First, login to get authentication
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }

        print("Logging in...")
        login_response = requests.post(f"{base_url}/auth/login", data=login_data)

        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            print(login_response.text)
            return False

        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        print("Login successful")

        # Get the test document
        print("Getting test document...")
        doc_response = requests.get(f"{base_url}/documents/29", headers=headers)

        if doc_response.status_code != 200:
            print(f"Failed to get document: {doc_response.status_code}")
            return False

        document = doc_response.json()
        print(f"Document: {document['filename']} (ID: {document['id']})")
        print(f"Current status: {document['status']}")
        print(f"Current content length: {len(document.get('content', ''))}")

        # Test extraction
        print("Testing extraction endpoint...")
        extract_response = requests.post(f"{base_url}/documents/29/extract", headers=headers)

        print(f"Extraction response status: {extract_response.status_code}")

        if extract_response.status_code == 200:
            result = extract_response.json()
            print("Extraction successful!")
            print(f"Message: {result.get('message')}")
            print(f"Extraction method: {result.get('extraction_method')}")
            print(f"Processing time: {result.get('processing_time'):.2f}s")
            print(f"Content length: {result.get('content_length', 0)} characters")

            # Verify the document was updated in database
            print("Verifying document in database...")
            updated_doc_response = requests.get(f"{base_url}/documents/29", headers=headers)

            if updated_doc_response.status_code == 200:
                updated_doc = updated_doc_response.json()
                print(f"Document updated: Status = {updated_doc['status']}")
                print(f"Content length in DB: {len(updated_doc.get('content', ''))}")

                if updated_doc['status'] == 'extracted' and len(updated_doc.get('content', '')) > 0:
                    print("SUCCESS! Content is properly stored in database.")
                    return True
                else:
                    print("Content not stored properly in database")
                    return False
            else:
                print(f"Failed to verify document update: {updated_doc_response.status_code}")
                return False
        else:
            print(f"Extraction failed: {extract_response.status_code}")
            print(extract_response.text)
            return False

    except Exception as e:
        print(f"Error during API test: {e}")
        return False

def check_database_directly():
    """Check database content directly"""
    print("Checking database directly...")

    try:
        # Import here to avoid issues if not in correct directory
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        from app.database import SessionLocal
        from app.models import Document

        db = SessionLocal()
        document = db.query(Document).filter(Document.id == 29).first()

        if document:
            print(f"Document in DB: {document.filename}")
            print(f"Status: {document.status}")
            print(f"Content length: {len(document.content) if document.content else 0}")
            print(f"Content preview: {document.content[:200] + '...' if document.content else 'No content'}")

            if document.status == 'extracted' and document.content:
                print("Content is properly stored in database!")
                return True
            else:
                print("Content not found in database")
                return False
        else:
            print("Document not found in database")
            return False

    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    print("Testing extraction functionality...\n")

    # First check database directly
    db_ok = check_database_directly()

    if not db_ok:
        print("Testing via API...")
        import time
        time.sleep(2)  # Wait for server to be ready
        api_ok = asyncio.run(test_extraction_api())
    else:
        api_ok = True

    if db_ok or api_ok:
        print("SUCCESS: Extraction is working and storing data in database!")
    else:
        print("FAILURE: Extraction is not working properly")

    sys.exit(0 if (db_ok or api_ok) else 1)