#!/usr/bin/env python3
"""
Script to create a new super admin user
"""
import sys
import os

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.auth import get_password_hash

def create_super_admin():
    """Create a new super admin user"""
    db = SessionLocal()

    try:
        # Get user details
        username = input("Enter username for new super admin: ").strip()
        email = input("Enter email for new super admin: ").strip()
        password = input("Enter password for new super admin: ").strip()

        if not username or not password:
            print("❌ Username and password are required")
            return

        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print(f"❌ User '{username}' already exists")
            return

        # Create super admin user
        super_admin = User(
            username=username,
            email=email if email else None,
            password_hash=get_password_hash(password),
            role="super_admin",
            is_active=True
        )

        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)

        print("✅ Super Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Role: super_admin")
        print(f"Password: {password}")
        print("")
        print("🔐 Login credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")

    except Exception as e:
        print(f"❌ Error creating super admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()