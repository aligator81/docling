import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_utils import authenticate_user, is_admin, is_user_active

def show_login_page():
    """Display the login page"""

    # Custom CSS for login page
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 3rem;
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
            color: #2c3e50;
        }
        .login-header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientShift 3s ease-in-out infinite;
        }
        .login-header p {
            color: #6c757d;
            font-size: 1.1rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-label {
            font-weight: 600;
            color: #495057;
            margin-bottom: 0.5rem;
            display: block;
        }
        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: white;
        }
        .login-btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        .register-link {
            text-align: center;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid #e9ecef;
        }
        .register-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.3s ease;
        }
        .register-link a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        .error-message {
            background: linear-gradient(145deg, #f8d7da, #f5c6cb);
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        .success-message {
            background: linear-gradient(145deg, #d4edda, #c3e6cb);
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        @keyframes gradientShift {
            0%, 100% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="login-header">
            <h1>📚 DocuMind</h1>
            <p>Document Q&A Assistant</p>
        </div>
    """, unsafe_allow_html=True)

    # Login form
    with st.form("login_form"):
        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="form-label">Username</label>', unsafe_allow_html=True)
        username = st.text_input("", placeholder="Enter your username", key="login_username", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="form-label">Password</label>', unsafe_allow_html=True)
        password = st.text_input("", placeholder="Enter your password", type="password", key="login_password", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        submit_button = st.form_submit_button("🔑 Login", use_container_width=True)

    # Handle login
    if submit_button:
        if not username or not password:
            st.error("❌ Please enter both username and password")
        else:
            with st.spinner("🔄 Authenticating..."):
                success, message, user_data = authenticate_user(username, password)

                if success and user_data:
                    # Store user data in session state
                    st.session_state.user_id = user_data["id"]
                    st.session_state.username = user_data["username"]
                    st.session_state.user_role = user_data["role"]
                    st.session_state.user_email = user_data["email"]
                    st.session_state.is_authenticated = True
                    st.session_state.last_login = str(user_data["last_login"])

                    st.success(f"✅ Welcome back, {username}!")

                    # Small delay for better UX
                    import time
                    time.sleep(0.5)

                    # Rerun to refresh the app state
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    # Registration link
    st.markdown("""
        <div class="register-link">
            <p>Don't have an account? <a href="#" onclick="document.getElementById('register_tab').click(); return false;">Create one here</a></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def show_register_page():
    """Display the registration page"""

    # Custom CSS for register page
    st.markdown("""
        <style>
        .register-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 3rem;
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }
        .register-header {
            text-align: center;
            margin-bottom: 2rem;
            color: #2c3e50;
        }
        .register-header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientShift 3s ease-in-out infinite;
        }
        .register-header p {
            color: #6c757d;
            font-size: 1.1rem;
        }
        .password-strength {
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        .strength-weak { color: #dc3545; }
        .strength-medium { color: #ffc107; }
        .strength-strong { color: #28a745; }
        .login-link {
            text-align: center;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid #e9ecef;
        }
        .login-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.3s ease;
        }
        .login-link a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="register-container">', unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="register-header">
            <h1>📚 DocuMind</h1>
            <p>Create New Account</p>
        </div>
    """, unsafe_allow_html=True)

    # Registration form
    with st.form("register_form"):
        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="form-label">Username</label>', unsafe_allow_html=True)
        username = st.text_input("", placeholder="Choose a username", key="reg_username", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="form-label">Email (Optional)</label>', unsafe_allow_html=True)
        email = st.text_input("", placeholder="Enter your email", key="reg_email", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="form-label">Password</label>', unsafe_allow_html=True)
        password = st.text_input("", placeholder="Create a password", type="password", key="reg_password", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<label class="form-label">Confirm Password</label>', unsafe_allow_html=True)
        confirm_password = st.text_input("", placeholder="Confirm your password", type="password", key="reg_confirm_password", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        submit_button = st.form_submit_button("📝 Create Account", use_container_width=True)

    # Handle registration
    if submit_button:
        # Validation
        errors = []

        if not username:
            errors.append("Username is required")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long")

        if password != confirm_password:
            errors.append("Passwords do not match")

        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Import here to avoid circular imports
            from auth_utils import create_user

            with st.spinner("🔄 Creating account..."):
                success, message = create_user(username, password, email if email else None)

                if success:
                    st.success(f"✅ {message}")
                    st.info("🔑 You can now login with your new account!")

                    # Small delay for better UX
                    import time
                    time.sleep(1)

                    # Switch back to login tab
                    st.session_state.show_login = True
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    # Login link
    st.markdown("""
        <div class="login-link">
            <p>Already have an account? <a href="#" onclick="document.getElementById('login_tab').click(); return false;">Login here</a></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def show_authentication_page():
    """Main authentication page with tabs for login and register"""

    # Set page config for auth page
    st.set_page_config(
        page_title="🔑 DocuMind - Login",
        page_icon="🔑",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Initialize session state for tab management
    if "show_login" not in st.session_state:
        st.session_state.show_login = True

    # Create tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        show_login_page()

    with tab2:
        show_register_page()

    # Hidden buttons for JavaScript navigation (fallback)
    if st.button("Login", key="login_tab", help="Switch to login tab"):
        st.session_state.show_login = True
        st.rerun()

    if st.button("Register", key="register_tab", help="Switch to register tab"):
        st.session_state.show_login = False
        st.rerun()