#!/usr/bin/env python3
"""
Script to create a default admin user for the authentication system.
Run this after creating the users table.
"""

import psycopg2
import os
import sys
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection string
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

if not NEON_CONNECTION_STRING:
    print("ERROR: NEON_CONNECTION_STRING environment variable is required!")
    print("Please set NEON_CONNECTION_STRING in your .env file.")
    sys.exit(1)

def create_default_admin():
    """Create a default admin user"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)

        with conn.cursor() as cur:
            # Check if any admin users exist
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cur.fetchone()[0]

            if admin_count > 0:
                print(f"SUCCESS: Found {admin_count} existing admin user(s)")
                print("No need to create a default admin user.")
                return True

            # Create default admin user
            print("Creating default admin user...")

            # Default credentials (you can change these)
            username = "admin"
            password = "AdminPass123!"  # Make sure to change this!
            email = None

            # Hash password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

            # Insert admin user
            cur.execute("""
                INSERT INTO users (username, password_hash, email, role, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (username, password_hash, email, "admin"))

            conn.commit()
            print(f"SUCCESS: Default admin user '{username}' created successfully!")
            print(f"Username: {username}")
            print(f"Password: {password}")
            print("IMPORTANT: Please change this password after first login!")

            return True

    except Exception as e:
        print(f"ERROR: Error creating admin user: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Creating default admin user...")
    print("=" * 40)

    if create_default_admin():
        print("\nAdmin user created successfully!")
        print("\nNext steps:")
        print("1. Run: streamlit run 5-chat.py")
        print("2. Login with username: admin")
        print("3. Use password: AdminPass123!")
        print("4. IMPORTANT: Change the password after first login!")
        print("5. Configure API keys (admin only)")
    else:
        print("\nFailed to create admin user!")
        print("Please check your database connection and try again.")
        sys.exit(1)