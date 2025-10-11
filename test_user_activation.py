#!/usr/bin/env python3
"""
Test script to verify user registration and activation workflow
"""
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}  # Adjust as needed
TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "password": "TestPass123"
}

def test_registration():
    """Test user registration creates inactive user"""
    print("🔹 Testing user registration...")

    response = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)

    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ User registered successfully: {user_data['username']}")
        print(f"   User ID: {user_data['id']}")
        print(f"   Is Active: {user_data['is_active']}")
        return user_data
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_login_inactive_user():
    """Test that inactive user cannot login"""
    print("\n🔹 Testing login with inactive user...")

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login",
                               data={"username": TEST_USER["username"], "password": TEST_USER["password"]})

        if response.status_code == 400:
            print("✅ Inactive user correctly blocked from login")
            print(f"   Error: {response.json()['detail']}")
            return True
        else:
            print(f"❌ Expected login to fail, but got: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error during inactive user test: {e}")
        return False

def test_admin_login():
    """Test admin login"""
    print("\n🔹 Testing admin login...")

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

def test_admin_activate_user(admin_token, user_id):
    """Test admin activating user"""
    print(f"\n🔹 Testing admin activation of user {user_id}...")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.put(f"{BASE_URL}/api/admin/users/{user_id}/status?is_active=true",
                          headers=headers)

    if response.status_code == 200:
        print("✅ User successfully activated by admin")
        print(f"   Response: {response.json()['message']}")
        return True
    else:
        print(f"❌ User activation failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_login_active_user():
    """Test that activated user can login"""
    print("\n🔹 Testing login with activated user...")

    response = requests.post(f"{BASE_URL}/api/auth/login",
                           data={"username": TEST_USER["username"], "password": TEST_USER["password"]})

    if response.status_code == 200:
        data = response.json()
        print("✅ Activated user login successful")
        print(f"   User: {data['user']['username']}")
        print(f"   Role: {data['user']['role']}")
        print(f"   Is Active: {data['user']['is_active']}")
        return True
    else:
        print(f"❌ Activated user login failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def main():
    """Run the complete test workflow"""
    print("🚀 Starting user registration and activation workflow test...\n")

    # Step 1: Register new user
    user_data = test_registration()
    if not user_data:
        print("\n❌ Test failed at registration step")
        return

    # Step 2: Verify inactive user cannot login
    if not test_login_inactive_user():
        print("\n❌ Test failed at inactive user login step")
        return

    # Step 3: Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print("\n❌ Test failed at admin login step")
        return

    # Step 4: Admin activates user
    if not test_admin_activate_user(admin_token, user_data["id"]):
        print("\n❌ Test failed at user activation step")
        return

    # Step 5: Verify activated user can login
    if not test_login_active_user():
        print("\n❌ Test failed at activated user login step")
        return

    print("\n🎉 All tests passed! User registration and activation workflow is working correctly.")

if __name__ == "__main__":
    main()