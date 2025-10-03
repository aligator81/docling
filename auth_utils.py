import bcrypt
import psycopg2
from psycopg2.extras import Json
import streamlit as st
from datetime import datetime
import re
import os
from typing import Optional, Dict, Any

# Database connection function (reused from main app)
def get_db_connection():
    """Get connection to Neon database"""
    try:
        # Use environment variable instead of session state for reliability
        conn_str = os.getenv("NEON_CONNECTION_STRING")
        if not conn_str:
            st.error("❌ NEON_CONNECTION_STRING environment variable not set!")
            return None
        conn = psycopg2.connect(conn_str)
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, "Password is strong"

def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"

    if len(username) > 50:
        return False, "Username must be less than 50 characters"

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, "Username is valid"

def validate_email(email: str) -> tuple[bool, str]:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, "Email is valid"
    return False, "Please enter a valid email address"

def create_user(username: str, password: str, email: str = None, role: str = "user") -> tuple[bool, str]:
    """Create a new user account"""
    # Validate inputs
    valid, message = validate_username(username)
    if not valid:
        return False, message

    valid, message = validate_password(password)
    if not valid:
        return False, message

    if email:
        valid, message = validate_email(email)
        if not valid:
            return False, message

    # Check if username already exists
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            # Check if username exists
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return False, "Username already exists"

            # Check if email exists (if provided)
            if email:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return False, "Email already exists"

            # Hash password and create user
            password_hash = hash_password(password)
            cur.execute("""
                INSERT INTO users (username, password_hash, email, role, created_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (username, password_hash, email, role, datetime.now(), False))

            user_id = cur.fetchone()[0]
            conn.commit()

            return True, f"User '{username}' created successfully"

    except Exception as e:
        return False, f"Error creating user: {str(e)}"
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> tuple[bool, str, Optional[Dict[str, Any]]]:
    """Authenticate a user with username and password"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed", None

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, password_hash, email, role, created_at, last_login, is_active
                FROM users
                WHERE username = %s
            """, (username,))

            user = cur.fetchone()

            if not user:
                return False, "Invalid username or password", None

            user_id, db_username, password_hash, email, role, created_at, last_login, is_active = user

            # Check if account is active
            if not is_active:
                return False, "Account is deactivated", None

            # Verify password
            if not verify_password(password, password_hash):
                return False, "Invalid username or password", None

            # Update last login time
            cur.execute("""
                UPDATE users
                SET last_login = %s
                WHERE id = %s
            """, (datetime.now(), user_id))

            conn.commit()

            # Return user data
            user_data = {
                "id": user_id,
                "username": db_username,
                "email": email,
                "role": role,
                "created_at": created_at,
                "last_login": last_login,
                "is_active": is_active
            }

            return True, "Login successful", user_data

    except Exception as e:
        return False, f"Authentication error: {str(e)}", None
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user data by ID"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users
                WHERE id = %s
            """, (user_id,))

            user = cur.fetchone()
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "role": user[3],
                    "created_at": user[4],
                    "last_login": user[5],
                    "is_active": user[6]
                }
            return None

    except Exception as e:
        st.error(f"Error getting user: {str(e)}")
        return None
    finally:
        conn.close()

def get_all_users() -> list:
    """Get all users (admin function)"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            """)

            users = []
            for user in cur.fetchall():
                users.append({
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "role": user[3],
                    "created_at": user[4],
                    "last_login": user[5],
                    "is_active": user[6]
                })

            return users

    except Exception as e:
        st.error(f"Error getting users: {str(e)}")
        return []
    finally:
        conn.close()

def update_user_role(user_id: int, new_role: str) -> tuple[bool, str]:
    """Update user role (admin function)"""
    if new_role not in ["admin", "user"]:
        return False, "Invalid role"

    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET role = %s
                WHERE id = %s
                RETURNING username
            """, (new_role, user_id))

            user = cur.fetchone()
            if user:
                conn.commit()
                return True, f"User '{user[0]}' role updated to {new_role}"
            else:
                return False, "User not found"

    except Exception as e:
        return False, f"Error updating user role: {str(e)}"
    finally:
        conn.close()

def deactivate_user(user_id: int) -> tuple[bool, str]:
    """Deactivate a user account (admin function)"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET is_active = FALSE
                WHERE id = %s
                RETURNING username
            """, (user_id,))

            user = cur.fetchone()
            if user:
                conn.commit()
                return True, f"User '{user[0]}' has been deactivated"
            else:
                return False, "User not found"

    except Exception as e:
        return False, f"Error deactivating user: {str(e)}"
    finally:
        conn.close()

def activate_user(user_id: int) -> tuple[bool, str]:
    """Activate a user account (admin function)"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users
                SET is_active = TRUE
                WHERE id = %s
                RETURNING username
            """, (user_id,))

            user = cur.fetchone()
            if user:
                conn.commit()
                return True, f"User '{user[0]}' has been activated"
            else:
                return False, "User not found"

    except Exception as e:
        return False, f"Error activating user: {str(e)}"
    finally:
        conn.close()

def is_admin(user_data: Dict[str, Any]) -> bool:
    """Check if user is an admin"""
    return user_data.get("role") == "admin"

def delete_user(user_id: int) -> tuple[bool, str]:
    """Delete a user account (admin function)"""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"

    try:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT username, role FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()

            if not user:
                return False, "User not found"

            username, role = user

            # Prevent deletion of the last admin user
            if role == "admin":
                cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND id != %s", (user_id,))
                admin_count = cur.fetchone()[0]
                if admin_count == 0:
                    return False, "Cannot delete the last admin user"

            # Delete user
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()

            return True, f"User '{username}' has been deleted successfully"

    except Exception as e:
        return False, f"Error deleting user: {str(e)}"
    finally:
        conn.close()

def is_user_active(user_data: Dict[str, Any]) -> bool:
    """Check if user account is active"""
    return user_data.get("is_active", False)