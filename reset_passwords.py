#!/usr/bin/env python3
"""
Password reset script for Docling App users
"""
from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.auth import get_password_hash

def reset_passwords():
    """Reset user passwords to known values"""
    db = SessionLocal()

    try:
        # Reset admin password (must be at least 6 characters for frontend validation)
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            admin_user.password_hash = get_password_hash("admin123")
            print("Admin password reset to: admin123")
        else:
            print("Admin user not found")

        # Reset testuser password (must be at least 6 characters for frontend validation)
        test_user = db.query(User).filter(User.username == "testuser").first()
        if test_user:
            test_user.password_hash = get_password_hash("test123")
            print("Test user password reset to: test123")
        else:
            print("Test user not found")

        # Commit changes
        db.commit()
        print("Password reset completed successfully!")

    except Exception as e:
        print(f"Error resetting passwords: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Resetting user passwords...")
    reset_passwords()