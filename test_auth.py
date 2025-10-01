#!/usr/bin/env python3
"""
Test script for the authentication system.
Run this script to test the authentication functionality before running the main app.
"""

import os
import sys
import getpass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")

    try:
        from auth_utils import get_db_connection

        conn = get_db_connection()
        if conn:
            print("✅ Database connection successful!")
            conn.close()
            return True
        else:
            print("❌ Database connection failed!")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_create_users_table():
    """Test creating users table"""
    print("\n🏗️ Testing users table creation...")

    try:
        from create_users_table import create_users_table

        if create_users_table():
            print("✅ Users table created successfully!")
            return True
        else:
            print("❌ Failed to create users table!")
            return False
    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        return False

def test_user_creation():
    """Test creating a user account"""
    print("\n👤 Testing user creation...")

    try:
        from auth_utils import create_user

        # Get user input
        username = input("Enter test username: ").strip()
        if not username:
            print("❌ Username is required!")
            return False

        email = input("Enter email (optional): ").strip() or None
        password = getpass.getpass("Enter password: ").strip()

        if not password:
            print("❌ Password is required!")
            return False

        success, message = create_user(username, password, email, "user")

        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def test_user_authentication():
    """Test user authentication"""
    print("\n🔑 Testing user authentication...")

    try:
        from auth_utils import authenticate_user

        username = input("Enter username to test: ").strip()
        if not username:
            print("❌ Username is required!")
            return False

        password = getpass.getpass("Enter password: ").strip()

        if not password:
            print("❌ Password is required!")
            return False

        success, message, user_data = authenticate_user(username, password)

        if success and user_data:
            print(f"✅ {message}")
            print(f"   User ID: {user_data['id']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Role: {user_data['role']}")
            print(f"   Email: {user_data['email']}")
            return True
        else:
            print(f"❌ {message}")
            return False

    except Exception as e:
        print(f"❌ Error authenticating user: {e}")
        return False

def test_admin_creation():
    """Test creating an admin user"""
    print("\n👑 Testing admin user creation...")

    try:
        from auth_utils import create_user

        # Get admin input
        username = input("Enter admin username: ").strip()
        if not username:
            print("❌ Username is required!")
            return False

        email = input("Enter admin email (optional): ").strip() or None
        password = getpass.getpass("Enter admin password: ").strip()

        if not password:
            print("❌ Password is required!")
            return False

        success, message = create_user(username, password, email, "admin")

        if success:
            print(f"✅ {message}")
            print(f"🔑 Admin user '{username}' created successfully!")
            return True
        else:
            print(f"❌ {message}")
            return False

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Authentication System Test Suite")
    print("=" * 50)

    # Check if NEON_CONNECTION_STRING is set
    if not os.getenv("NEON_CONNECTION_STRING"):
        print("❌ NEON_CONNECTION_STRING environment variable is not set!")
        print("Please set it in your .env file before running tests.")
        return

    tests = [
        ("Database Connection", test_database_connection),
        ("Create Users Table", test_create_users_table),
        ("Create Test User", test_user_creation),
        ("User Authentication", test_user_authentication),
        ("Create Admin User", test_admin_creation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Test interrupted by user")
            break
        except Exception as e:
            print(f"💥 Unexpected error in {test_name}: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Authentication system is ready.")
        print("\nNext steps:")
        print("1. Run: streamlit run 5-chat.py")
        print("2. Login with your admin credentials")
        print("3. Configure API keys (admin only)")
        print("4. Create additional user accounts as needed")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("Make sure your database is running and accessible.")

if __name__ == "__main__":
    main()