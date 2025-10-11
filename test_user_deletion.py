#!/usr/bin/env python3
"""
Test script to verify user deletion functionality
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

def test_delete_user(admin_token, user_id):
    """Test deleting a user"""
    print(f"\n🔹 Testing user deletion for user ID {user_id}...")

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.delete(f"{BASE_URL}/api/admin/users/{user_id}",
                              headers=headers)

    if response.status_code == 200:
        print("✅ User successfully deleted")
        print(f"   Response: {response.json()['message']}")
        return True
    else:
        print(f"❌ User deletion failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_verify_user_deleted(user_id):
    """Test that deleted user no longer exists"""
    print(f"\n🔹 Verifying user {user_id} no longer exists...")

    # Try to get user list
    response = requests.get(f"{BASE_URL}/api/admin/users")

    if response.status_code == 200:
        users = response.json()
        user_exists = any(user['id'] == user_id for user in users)

        if not user_exists:
            print(f"✅ User {user_id} successfully removed from system")
            return True
        else:
            print(f"❌ User {user_id} still exists in system")
            return False
    else:
        print(f"❌ Failed to get user list: {response.status_code}")
        return False

def main():
    """Run the user deletion test"""
    print("🚀 Testing user deletion functionality...\n")

    # Admin login
    admin_token = test_admin_login()
    if not admin_token:
        print("\n❌ Test failed at admin login step")
        return

    # For testing, we'll delete user with ID 17 (the one created in our previous test)
    # In a real scenario, you'd want to create a test user first
    test_user_id = 17

    # Delete user
    if test_delete_user(admin_token, test_user_id):
        # Verify deletion
        if test_verify_user_deleted(test_user_id):
            print("\n🎉 User deletion functionality is working correctly!")
        else:
            print("\n❌ User deletion verification failed")
    else:
        print("\n❌ User deletion test failed")

if __name__ == "__main__":
    main()