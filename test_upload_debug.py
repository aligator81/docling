import requests
import os
from pathlib import Path

# Test script to debug file upload issues

def create_test_png():
    """Create a simple test PNG file"""
    # Create a minimal valid PNG file (1x1 pixel transparent PNG)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

    with open('test.png', 'wb') as f:
        f.write(png_data)

    print(f"✅ Created test.png ({len(png_data)} bytes)")
    return 'test.png'

def test_upload():
    """Test the upload endpoint"""
    # First check if file validation is enabled
    print("🔍 Checking environment variables...")
    file_validation = os.getenv("FILE_VALIDATION_ENABLED", "false")
    print(f"FILE_VALIDATION_ENABLED: {file_validation}")

    # Create test PNG file
    test_file = create_test_png()

    # Check file details
    file_size = Path(test_file).stat().st_size
    print(f"📄 Test file size: {file_size} bytes")

    # Try to read first few bytes to check PNG signature
    with open(test_file, 'rb') as f:
        header = f.read(16)
        print(f"📄 PNG header (first 16 bytes): {header.hex()}")

    # Check if PNG signature is correct
    png_signature = b'\x89PNG\r\n\x1a\n'
    if header.startswith(png_signature):
        print("✅ Valid PNG signature detected")
    else:
        print("❌ Invalid PNG signature")

    # Try upload without authentication first to see if endpoint exists
    print("\n🔄 Testing upload endpoint (without auth)...")

    try:
        with open(test_file, 'rb') as f:
            response = requests.post('http://localhost:8000/api/documents/upload',
                                   files={'file': (test_file, f, 'image/png')})

        print(f"Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ Upload endpoint exists! (401 is expected without auth)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

    # Get auth token for authenticated test
    print("\n🔐 Attempting to login for authenticated test...")
    try:
        login_response = requests.post('http://localhost:8000/api/auth/login',
                                     data={'username': 'admin', 'password': 'admin123'})
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('access_token')
            print("✅ Login successful")

            # Test upload with authentication
            print("\n🔄 Testing authenticated upload...")
            headers = {'Authorization': f'Bearer {token}'}

            with open(test_file, 'rb') as f:
                response = requests.post('http://localhost:8000/api/documents/upload',
                                       files={'file': (test_file, f, 'image/png')},
                                       headers=headers)

            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Upload successful!")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Upload failed with status: {response.status_code}")
                print(f"Response: {response.text}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")

    except Exception as e:
        print(f"❌ Error during authenticated test: {e}")

    # Clean up
    try:
        os.remove(test_file)
        print(f"\n🧹 Cleaned up {test_file}")
    except:
        pass

if __name__ == "__main__":
    test_upload()