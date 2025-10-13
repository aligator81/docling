#!/usr/bin/env python3
"""
Test script for concurrent document processing capabilities
"""

import asyncio
import aiohttp
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_FILES = [
    "backend/test.png",  # Assuming this exists
]

async def test_concurrent_uploads(num_uploads: int = 3):
    """Test concurrent document uploads and processing"""

    # First, we need to authenticate and get a token
    login_data = {
        "username": "admin",
        "password": "secure-admin-password"
    }

    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(f"{BASE_URL}/api/auth/login", json=login_data) as response:
            if response.status != 200:
                print("❌ Login failed")
                return

            login_result = await response.json()
            token = login_result["access_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        # Create test files if they don't exist
        for i in range(num_uploads):
            test_file = f"test_upload_{i}.txt"
            if not os.path.exists(test_file):
                with open(test_file, "w") as f:
                    f.write(f"Test document {i} for concurrent processing test.\n" * 50)

        print(f"🚀 Starting concurrent upload test with {num_uploads} documents")

        start_time = time.time()

        # Upload documents concurrently
        upload_tasks = []
        for i in range(num_uploads):
            test_file = f"test_upload_{i}.txt"
            if os.path.exists(test_file):
                upload_tasks.append(upload_document(session, test_file, headers))

        # Wait for all uploads to complete
        upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)

        upload_time = time.time() - start_time

        # Check results
        successful_uploads = 0
        document_ids = []

        for i, result in enumerate(upload_results):
            if isinstance(result, Exception):
                print(f"❌ Upload {i} failed: {result}")
            else:
                successful_uploads += 1
                document_ids.append(result.get("document_id"))
                print(f"✅ Upload {i} successful: Document ID {result.get('document_id')}")

        print("📊 Upload Results:")
        print(f"   Total uploads: {num_uploads}")
        print(f"   Successful: {successful_uploads}")
        print(f"   Failed: {num_uploads - successful_uploads}")
        print(f"   Time taken: {upload_time:.2f} seconds")
        print(f"   Average time per upload: {upload_time/num_uploads:.2f} seconds")

        # Test status checking
        if document_ids:
            print("🔍 Checking processing status...")
            await asyncio.sleep(2)  # Wait a bit for processing to start

            for doc_id in document_ids[:2]:  # Check first 2 documents
                await check_processing_status(session, doc_id, headers)

        # Cleanup test files
        for i in range(num_uploads):
            test_file = f"test_upload_{i}.txt"
            try:
                os.remove(test_file)
            except:
                pass

        return successful_uploads == num_uploads

async def upload_document(session, file_path: str, headers: dict) -> dict:
    """Upload a single document"""
    try:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=os.path.basename(file_path))

            async with session.post(
                f"{BASE_URL}/api/documents/upload",
                data=data,
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}"}
    except Exception as e:
        return {"error": str(e)}

async def check_processing_status(session, document_id: int, headers: dict):
    """Check the processing status of a document"""
    try:
        async with session.get(
            f"{BASE_URL}/api/documents/{document_id}/processing-status",
            headers=headers
        ) as response:
            if response.status == 200:
                status_data = await response.json()
                print(f"📊 Document {document_id} status: {status_data.get('status', 'unknown')}")
                return status_data
            else:
                print(f"❌ Failed to get status for document {document_id}")
    except Exception as e:
        print(f"❌ Error checking status for document {document_id}: {e}")

async def test_queue_status(session, headers: dict):
    """Test the queue status endpoint (admin only)"""
    try:
        async with session.get(
            f"{BASE_URL}/api/documents/processing/queue-status",
            headers=headers
        ) as response:
            if response.status == 200:
                queue_data = await response.json()
                print("📊 Queue Status:"                print(f"   Queue size: {queue_data.get('queue_size', 0)}")
                print(f"   Active jobs: {queue_data.get('active_jobs', 0)}")
                print(f"   Max workers: {queue_data.get('max_workers', 0)}")
                return queue_data
            else:
                print(f"❌ Failed to get queue status: HTTP {response.status}")
    except Exception as e:
        print(f"❌ Error getting queue status: {e}")

async def main():
    """Main test function"""
    print("🧪 Testing Concurrent Document Processing")
    print("=" * 50)

    # Test 1: Concurrent uploads
    print("\n1️⃣ Testing concurrent uploads...")
    success = await test_concurrent_uploads(3)

    if success:
        print("✅ Concurrent upload test passed!")
    else:
        print("❌ Concurrent upload test failed!")

    # Test 2: Queue status (requires admin)
    print("\n2️⃣ Testing queue status...")
    async with aiohttp.ClientSession() as session:
        login_data = {"username": "admin", "password": "secure-admin-password"}
        async with session.post(f"{BASE_URL}/api/auth/login", json=login_data) as response:
            if response.status == 200:
                login_result = await response.json()
                token = login_result["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                await test_queue_status(session, headers)

    print("\n🎉 Concurrent processing test completed!")

if __name__ == "__main__":
    asyncio.run(main())