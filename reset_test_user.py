#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from passlib.context import CryptContext

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

    # Hash the password
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("testpassword123")

    # Update testuser password
    result = db.execute(text("""
        UPDATE users
        SET password_hash = :password
        WHERE username = :username
    """), {
        "username": "testuser",
        "password": hashed_password
    })

    db.commit()

    if result.rowcount > 0:
        print("SUCCESS: Test user password reset successfully!")
        print("Username: testuser")
        print("Password: testpassword123")
    else:
        print("WARNING: Test user not found")

    db.close()

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)