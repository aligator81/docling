import requests
import os

# Test file upload functionality
def test_file_upload():
    # API endpoint
    url = "http://localhost:8000/api/documents/upload"
    
    # Test with a PDF file
    files = {'file': ('test.pdf', open('test_upload.py', 'rb'), 'application/pdf')}
    
    # Add auth token (you'll need to get this from your login)
    headers = {
        'Authorization': 'Bearer YOUR_TOKEN_HERE'  # Replace with actual token
    }
    
    try:
        response = requests.post(url, files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ File upload successful!")
        else:
            print("❌ File upload failed")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing file upload functionality...")
    test_file_upload()