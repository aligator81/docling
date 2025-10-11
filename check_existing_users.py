#!/usr/bin/env python3
"""
Script to check existing users and help with registration testing
"""
import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def admin_login():
    """Login as admin to get access token"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login",
                               data=ADMIN_CREDENTIALS)

        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error during admin login: {e}")
        return None

def check_existing_users():
    """Check what users currently exist in the system"""
    print("🔍 Checking existing users...")

    # First login as admin
    token = admin_login()
    if not token:
        print("❌ Cannot check users: Admin login failed")
        return []

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)

        if response.status_code == 200:
            users = response.json()
            print(f"✅ Found {len(users)} users in the system:")

            for user in users:
                print(f"   ID: {user['id']}")
                print(f"   Username: {user['username']}")
                print(f"   Email: {user['email'] or 'N/A'}")
                print(f"   Role: {user['role']}")
                print(f"   Active: {user['is_active']}")
                print(f"   Created: {user['created_at'][:10] if user['created_at'] else 'Unknown'}")
                print("   ---")

            return users
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            print(f"   Error: {response.text}")
            return []

    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("   Make sure the backend server is running on port 8000")
        return []

def suggest_test_username(existing_users):
    """Suggest a unique username for testing"""
    base_names = ["testuser", "newuser", "demo", "sample"]
    timestamp = str(int(__import__("time").time()))[-6:]  # Last 6 digits of timestamp

    for base_name in base_names:
        test_username = f"{base_name}_{timestamp}"
        if not any(user['username'] == test_username for user in existing_users):
            return test_username

    # If all else fails, use timestamp only
    return f"user_{timestamp}"

def main():
    """Main function"""
    print("🚀 User Registration Helper\n")

    users = check_existing_users()

    if not users:
        print("\n💡 No users found or cannot connect to server.")
        print("   Make sure the backend server is running.")
        return

    print(f"\n💡 Found {len(users)} existing users.")
    print("   If you're getting 'Username or email already registered' errors,")
    print("   try one of these solutions:")

    print("\n1️⃣  Use a different username for testing:")
    suggested_username = suggest_test_username(users)
    print(f"   Suggested username: '{suggested_username}'")

    print("\n2️⃣  Delete test users through the admin panel:")
    print("   Go to: http://localhost:3000/admin/users")
    print("   Delete users you don't need (except 'admin')")

    print("\n3️⃣  Check if your desired username is available above")
    print("   The registration system correctly prevents duplicate users.")

    print(f"\n📋 Existing usernames: {', '.join([user['username'] for user in users])}")

if __name__ == "__main__":
    main()