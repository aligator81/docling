#!/usr/bin/env python3
"""
Database migration script to create the users table for authentication.
Run this script once to set up the authentication system.
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection string
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

if not NEON_CONNECTION_STRING:
    print("ERROR: NEON_CONNECTION_STRING environment variable is required!")
    print("Please set NEON_CONNECTION_STRING in your .env file.")
    sys.exit(1)

def create_users_table():
    """Create the users table for authentication"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)

        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT FALSE
                );
            """)

            # Create index on username for faster lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """)

            # Create index on email for faster lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """)

            # Create index on role for admin queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            """)

            conn.commit()
            print("SUCCESS: Users table created successfully!")

            # Check if we need to create a default admin user
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cur.fetchone()[0]

            if admin_count == 0:
                print("\nNOTE: No admin users found. Let's create a default admin user.")
                print("This is required for the application to work properly.")

                # Get admin credentials from user
                print("\nPlease provide details for the default admin user:")
                username = input("Username (default: admin): ").strip() or "admin"
                email = input("Email (optional): ").strip() or None
                password = input("Password (min 8 chars): ").strip()

                if len(password) < 8:
                    print("ERROR: Password must be at least 8 characters long!")
                    return False

                # Validate password strength
                import re
                if not re.search(r'[A-Z]', password):
                    print("ERROR: Password must contain at least one uppercase letter!")
                    return False

                if not re.search(r'[a-z]', password):
                    print("ERROR: Password must contain at least one lowercase letter!")
                    return False

                if not re.search(r'\d', password):
                    print("ERROR: Password must contain at least one number!")
                    return False

                # Hash password and create admin user
                import bcrypt
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

                cur.execute("""
                    INSERT INTO users (username, password_hash, email, role, created_at, is_active)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                """, (username, password_hash, email, "admin", True))

                conn.commit()
                print(f"SUCCESS: Default admin user '{username}' created successfully!")
                print("LOGIN: You can now login with these credentials.")

            else:
                print(f"SUCCESS: Found {admin_count} existing admin user(s)")

        return True

    except Exception as e:
        print(f"ERROR: Error creating users table: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_existing_tables():
    """Check what tables already exist in the database"""
    try:
        conn = psycopg2.connect(NEON_CONNECTION_STRING)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('users', 'documents', 'document_chunks', 'embeddings')
                ORDER BY table_name;
            """)

            tables = cur.fetchall()
            if tables:
                print("INFO: Existing tables in database:")
                for table in tables:
                    print(f"  * {table[0]}")
            else:
                print("INFO: No relevant tables found in database")

        conn.close()

    except Exception as e:
        print(f"ERROR: Error checking existing tables: {e}")

if __name__ == "__main__":
    print("Setting up authentication system...")
    print("=" * 50)

    # Check existing tables first
    check_existing_tables()
    print()

    # Create users table
    if create_users_table():
        print("\nSUCCESS: Authentication system setup complete!")
        print("\nNext steps:")
        print("1. Run your Streamlit application")
        print("2. Login with the admin credentials you created")
        print("3. Configure API keys (admin only)")
        print("4. Create additional user accounts as needed")
    else:
        print("\nERROR: Authentication system setup failed!")
        print("Please check your database connection and try again.")
        sys.exit(1)