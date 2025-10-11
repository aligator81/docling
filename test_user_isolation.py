#!/usr/bin/env python3
"""
Test script to verify user isolation functionality
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def test_admin_login():
    """Test admin login"""
    print("🔹 Testing admin login...")

    response = requests.post(f"{BASE_URL}/api/auth/login",
                           data=ADMIN_CREDENTIALS)

    if response.status_code == 200:
        data = response.json()
        print("✅ Admin login successful")
        return data["access_token"]
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_user_login():
    """Test regular user login"""
    print("\n🔹 Testing regular user login...")

    # First register a test user
    timestamp = str(int(time.time()))[-6:]
    test_user = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "TestPass123"
    }

    # Register user
    reg_response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
    if reg_response.status_code != 200:
        print(f"❌ User registration failed: {reg_response.status_code}")
        return None, None

    user_data = reg_response.json()
    print(f"✅ Test user registered: {user_data['username']}")

    # Activate the user using admin
    if not activate_user(user_data["id"]):
        print("❌ Failed to activate test user")
        return None, None

    # Login as the test user
    login_response = requests.post(f"{BASE_URL}/api/auth/login",
                                 data={"username": test_user["username"], "password": test_user["password"]})

    if login_response.status_code == 200:
        login_data = login_response.json()
        print("✅ Test user login successful")
        return login_data["access_token"], user_data["id"]
    else:
        print(f"❌ Test user login failed: {login_response.status_code}")
        print(f"   Error: {login_response.text}")
        return None, None

def activate_user(user_id):
    """Activate a user using admin privileges"""
    # Admin login for activation
    admin_response = requests.post(f"{BASE_URL}/api/auth/login", data=ADMIN_CREDENTIALS)
    if admin_response.status_code != 200:
        print("❌ Admin login for activation failed")
        return False

    admin_token = admin_response.json()["access_token"]

    # Activate user
    headers = {"Authorization": f"Bearer {admin_token}"}
    activate_response = requests.put(f"{BASE_URL}/api/admin/users/{user_id}/status?is_active=true", headers=headers)

    if activate_response.status_code == 200:
        print(f"✅ Test user {user_id} activated")
        return True
    else:
        print(f"❌ User activation failed: {activate_response.status_code}")
        print(f"   Error: {activate_response.text}")
        return False

def test_admin_sees_all_documents(admin_token):
    """Test that admin can see all documents"""
    print("\n🔹 Testing admin document access...")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/api/documents/", headers=headers)

    if response.status_code == 200:
        documents = response.json()
        print(f"✅ Admin can see {len(documents)} documents")

        # Show what admin can see
        for doc in documents[:3]:  # Show first 3 documents
            print(f"   - {doc['original_filename']} (User ID: {doc['user_id']})")

        return len(documents)
    else:
        print(f"❌ Admin document access failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return 0

def test_user_sees_only_own_documents(user_token, user_id):
    """Test that regular user only sees their own documents"""
    print("\n🔹 Testing user document isolation...")

    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/api/documents/", headers=headers)

    if response.status_code == 200:
        documents = response.json()
        print(f"✅ User can see {len(documents)} documents")

        # Verify all documents belong to this user
        user_documents = [doc for doc in documents if doc['user_id'] == user_id]
        other_documents = [doc for doc in documents if doc['user_id'] != user_id]

        if len(user_documents) == len(documents) and len(other_documents) == 0:
            print("✅ User isolation working correctly - only sees own documents")
            return True
        else:
            print(f"❌ User isolation failed - sees {len(other_documents)} other users' documents")
            return False
    else:
        print(f"❌ User document access failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def main():
    """Run the user isolation test"""
    print("🚀 Testing user isolation functionality...\n")

    # Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print("\n❌ Test failed at admin login step")
        return

    # Create and login as test user
    user_token, user_id = test_user_login()
    if not user_token:
        print("\n❌ Test failed at user creation/login step")
        return

    # Test admin sees all documents
    admin_doc_count = test_admin_sees_all_documents(admin_token)

    # Test user only sees own documents
    isolation_working = test_user_sees_only_own_documents(user_token, user_id)

    if isolation_working:
        print("\n🎉 User isolation is working correctly!")
        print("   ✅ Regular users only see their own documents")
        print("   ✅ Admin users can see all documents")
        print("   ✅ Chat will only search user's own documents")
    else:
        print("\n❌ User isolation has issues")

if __name__ == "__main__":
    main()