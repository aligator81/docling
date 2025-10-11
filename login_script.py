#!/usr/bin/env python3
"""
Login script to establish authentication session for the Docling App
"""
import requests
import json

# API configuration
API_BASE = "http://localhost:8000"

def login(username: str, password: str):
    """Login and return the authentication token and user data"""
    login_url = f"{API_BASE}/api/auth/login"

    # Prepare form data (as the backend expects form data)
    data = {
        "username": username,
        "password": password
    }

    print(f"Attempting to login as: {username}")

    try:
        response = requests.post(login_url, data=data)
        response.raise_for_status()

        result = response.json()
        token = result["access_token"]
        user = result["user"]

        print("Login successful!")
        print(f"   User: {user['username']} (role: {user['role']})")
        print(f"   Token: {token[:20]}...")

        return token, user

    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error = e.response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Status code: {e.response.status_code}")
        return None, None

def test_authentication(token: str):
    """Test the authentication by calling the /me endpoint"""
    me_url = f"{API_BASE}/api/auth/me"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(me_url, headers=headers)
        response.raise_for_status()

        user = response.json()
        print("Authentication test successful!")
        print(f"   Current user: {user['username']}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    print("Docling App Login Script")
    print("=" * 40)

    # Try admin login first
    print("\n1. Trying admin login...")
    token, user = login("admin", "admin")

    if token:
        print("\n2. Testing authentication...")
        if test_authentication(token):
            print("\nSuccess! You can now use the app with authentication.")
            print("   The frontend should work properly now.")
        else:
            print("\nWarning: Login succeeded but authentication test failed.")
    else:
        print("\nAdmin login failed. The users might not exist or have different passwords.")
        print("\nPlease check the web interface at http://localhost:3000")
        print("and try logging in manually with the correct credentials.")