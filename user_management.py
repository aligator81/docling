import streamlit as st
import pandas as pd
from datetime import datetime

# Import auth utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_utils import (
    get_all_users, update_user_role, deactivate_user, activate_user,
    is_admin, create_user, validate_username, validate_email, validate_password, delete_user
)

def show_user_management():
    """Display the admin user management interface"""

    st.markdown("### 👥 User Management")
    st.markdown("Manage user accounts, roles, and permissions.")

    # Check if current user is admin
    user_role = st.session_state.get("user_role", "")
    if user_role != "admin":
        st.error("❌ Access denied. Admin privileges required.")
        return

    # Get all users
    users = get_all_users()

    if not users:
        st.warning("⚠️ No users found in the system.")
        return

    # User statistics
    total_users = len(users)
    active_users = len([u for u in users if u["is_active"]])
    admin_users = len([u for u in users if u["role"] == "admin"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", total_users)
    with col2:
        st.metric("Active Users", active_users)
    with col3:
        st.metric("Admin Users", admin_users)

    # Create user DataFrame for display
    user_df = pd.DataFrame(users)
    user_df["created_at"] = pd.to_datetime(user_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    user_df["last_login"] = user_df["last_login"].apply(
        lambda x: pd.to_datetime(x).strftime("%Y-%m-%d %H:%M") if x and str(x) != 'NaT' else "Never"
    )

    # Custom styling for the table
    st.markdown("""
        <style>
        .user-table {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 15px;
            padding: 1rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid rgba(255, 255, 255, 0.8);
        }
        .user-row {
            padding: 1rem;
            border-bottom: 1px solid #e9ecef;
            transition: background-color 0.3s ease;
        }
        .user-row:hover {
            background-color: rgba(102, 126, 234, 0.05);
        }
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-active {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
        }
        .status-inactive {
            background: linear-gradient(45deg, #dc3545, #fd7e14);
            color: white;
        }
        .role-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .role-admin {
            background: linear-gradient(45deg, #6f42c1, #e83e8c);
            color: white;
        }
        .role-user {
            background: linear-gradient(45deg, #007bff, #6610f2);
            color: white;
        }
        .action-btn {
            margin: 0.25rem;
            border-radius: 8px;
            font-size: 0.8rem;
            padding: 0.5rem 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="user-table">', unsafe_allow_html=True)

    # Display users with management options
    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])

            with col1:
                st.markdown(f"**👤 {user['username']}**")
                if user['email']:
                    st.caption(f"📧 {user['email']}")

            with col2:
                st.caption(f"📅 Created: {user['created_at']}")
                st.caption(f"🔑 Last login: {user['last_login']}")

            with col3:
                # Role badge
                role_class = "role-admin" if user['role'] == "admin" else "role-user"
                st.markdown(f'<span class="role-badge {role_class}">{user["role"]}</span>', unsafe_allow_html=True)

            with col4:
                # Status badge
                status_class = "status-active" if user['is_active'] else "status-inactive"
                status_text = "Active" if user['is_active'] else "Inactive"
                st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)

            with col5:
                # Action buttons
                if user['id'] != st.session_state.get("user_id"):  # Don't allow self-management
                    # Use container instead of nested columns to avoid sidebar restrictions
                    with st.container():
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            if user['role'] == "user":
                                if st.button("👑 Promote", key=f"promote_{user['id']}", help=f"Make {user['username']} an admin"):
                                    success, message = update_user_role(user['id'], "admin")
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                            else:
                                if st.button("👤 Demote", key=f"demote_{user['id']}", help=f"Make {user['username']} a regular user"):
                                    success, message = update_user_role(user['id'], "user")
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")

                        with col2:
                            if user['is_active']:
                                if st.button("🚫 Deactivate", key=f"deactivate_{user['id']}", help=f"Deactivate {user['username']}'s account"):
                                    success, message = deactivate_user(user['id'])
                                    if success:
                                        st.warning(f"⚠️ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                            else:
                                if st.button("✅ Activate", key=f"activate_{user['id']}", help=f"Activate {user['username']}'s account"):
                                    success, message = activate_user(user['id'])
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")

                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{user['id']}", help=f"Delete {user['username']}'s account"):
                                if st.session_state.get(f"confirm_delete_{user['id']}", False):
                                    # Perform deletion
                                    success, message = delete_user(user['id'])
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                    # Reset confirmation state
                                    st.session_state[f"confirm_delete_{user['id']}"] = False
                                else:
                                    st.warning(f"⚠️ Click again to confirm deletion of '{user['username']}'")
                                    st.session_state[f"confirm_delete_{user['id']}"] = True

                            # Reset confirmation button (only show when confirmation is active)
                            if st.session_state.get(f"confirm_delete_{user['id']}", False):
                                if st.button("❌ Cancel", key=f"cancel_delete_{user['id']}", help="Cancel deletion"):
                                    st.session_state[f"confirm_delete_{user['id']}"] = False
                                    st.rerun()
                else:
                    st.caption("🔒 Cannot modify own account")

    st.markdown('</div>', unsafe_allow_html=True)

    # Create new user section
    st.markdown("---")
    st.markdown("### ➕ Create New User")

    with st.expander("📝 Add New User Account", expanded=False):
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_username = st.text_input("Username *", help="Required. 3-50 characters, letters/numbers/underscores/hyphens only")
                new_email = st.text_input("Email", help="Optional. Must be unique if provided")

            with col2:
                new_password = st.text_input("Password *", type="password", help="Required. Minimum 8 characters with uppercase, lowercase, number, and special character")
                new_role = st.selectbox("Role", ["user", "admin"], help="Admin users have full system access")

            submit_user = st.form_submit_button("👤 Create User", use_container_width=True)

        if submit_user:
            if not new_username or not new_password:
                st.error("❌ Username and password are required")
            else:
                # Validate inputs
                valid, message = validate_username(new_username)
                if not valid:
                    st.error(f"❌ {message}")
                else:
                    valid, message = validate_password(new_password)
                    if not valid:
                        st.error(f"❌ {message}")
                    else:
                        if new_email:
                            valid, message = validate_email(new_email)
                            if not valid:
                                st.error(f"❌ {message}")
                            else:
                                # Create user
                                success, message = create_user(new_username, new_password, new_email, new_role)
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        else:
                            # Create user without email
                            success, message = create_user(new_username, new_password, None, new_role)
                            if success:
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

    # Bulk operations
    st.markdown("---")
    st.markdown("### 📊 Bulk Operations")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Export Users", use_container_width=True):
            # Create export DataFrame
            export_df = user_df.copy()
            export_df = export_df.drop(columns=['id'])  # Remove sensitive ID column

            # Convert to CSV
            csv_data = export_df.to_csv(index=False)

            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col2:
        st.info("📋 Import functionality coming soon")

def show_current_user_info():
    """Display current user information in sidebar"""

    if not st.session_state.get("is_authenticated", False):
        return

    user_data = {
        "id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
        "email": st.session_state.get("user_email"),
        "role": st.session_state.get("user_role"),
        "last_login": st.session_state.get("last_login")
    }

    st.markdown("---")
    st.markdown("### 👤 Current User")

    # User avatar/icon
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(45deg, #667eea, #764ba2); display: inline-flex; align-items: center; justify-content: center; font-size: 24px; color: white; margin: 0 auto;">
                {user_data['username'][0].upper()}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**{user_data['username']}**")
    if user_data['email']:
        st.caption(f"📧 {user_data['email']}")

    # Role badge
    role_color = "#6f42c1" if user_data['role'] == "admin" else "#007bff"
    st.markdown(f"""
        <div style="background: {role_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; text-align: center; margin: 0.5rem 0;">
            {user_data['role']}
        </div>
    """, unsafe_allow_html=True)

    if user_data['last_login'] and user_data['last_login'] != "None":
        st.caption(f"🔑 Last login: {user_data['last_login']}")

    # Logout button
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        # Clear all session data
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.success("✅ Logged out successfully!")
        st.rerun()