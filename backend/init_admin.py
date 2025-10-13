#!/usr/bin/env python3
"""
Script to initialize an admin user for testing user management functionality.
"""
import sys
import os

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

def init_admin_user():
    """Create an admin user if it doesn't exist"""
    db = SessionLocal()

    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("Admin user already exists")
            return

        # Create super admin user
        super_admin = User(
            username="superadmin",
            email="superadmin@example.com",
            password_hash=get_password_hash("superadmin123"),
            role="super_admin",
            is_active=True
        )

        db.add(super_admin)
        db.commit()
        print("Super Admin user created successfully")
        print("Username: superadmin")
        print("Password: superadmin123")

        # Create a test user as well
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("test123"),
            role="user",
            is_active=True
        )

        db.add(test_user)
        db.commit()
        print("Test user created successfully")
        print("Username: testuser")
        print("Password: test123")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_admin_user()