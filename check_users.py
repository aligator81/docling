#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("NEON_CONNECTION_STRING")

if not DATABASE_URL:
    print("Error: NEON_CONNECTION_STRING not found in environment variables")
    sys.exit(1)

try:
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Check if users table exists and count users
    result = db.execute(text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()

    print(f"Found {user_count} users in database")

    if user_count == 0:
        print("No users found. Creating a test user...")

        # Create test user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        hashed_password = pwd_context.hash("testpassword123")

        # Insert test user
        db.execute(text("""
            INSERT INTO users (username, password_hash, email, role, is_active)
            VALUES (:username, :password, :email, :role, :is_active)
        """), {
            "username": "testuser",
            "password": hashed_password,
            "email": "test@example.com",
            "role": "user",
            "is_active": True
        })

        db.commit()
        print("Test user created successfully!")
        print("Username: testuser")
        print("Password: testpassword123")
    else:
        # Show existing users (without passwords)
        result = db.execute(text("SELECT id, username, email, role, is_active FROM users LIMIT 5"))
        users = result.fetchall()
        print("\nExisting users:")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}, Active: {user[4]}")

    db.close()

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)