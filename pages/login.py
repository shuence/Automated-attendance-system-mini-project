"""
Login page for the Attendance System.
"""
import streamlit as st
from utils.auth_utils import authenticate_user, ROLES
from utils.session_utils import save_session_token

def show_login_page():
    """Display the login page"""
    # Hide sidebar for login page
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        .stApp > header {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login page
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main title
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🔐 Login</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #666;'>Facial Attendance System</h3>", unsafe_allow_html=True)
        st.markdown("---")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>Enter your credentials</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember Me", value=True, help="Stay logged in for 30 days")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
            with col_btn2:
                st.form_submit_button("Clear", use_container_width=True)
            
            if login_button:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                else:
                    # Authenticate user
                    user = authenticate_user(username, password)
                    
                    if user:
                        # Store user in session state
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        
                        # Save session token for persistent login
                        try:
                            token = save_session_token(username, user, remember_me)
                            if token:
                                st.session_state.session_token = token
                                st.session_state.token_checked = True
                                
                                # Always save token to localStorage (for session persistence)
                                # This allows the session to persist across page refreshes
                                save_token_script = f"""
                                <script>
                                localStorage.setItem('attendance_session_token', '{token}');
                                </script>
                                """
                                st.components.v1.html(save_token_script, height=0)
                        except Exception as e:
                            # If session saving fails, continue with regular login
                            pass
                        
                        st.success(f"✅ Welcome, {user['name']} ({user['role']})!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Invalid username or password. Please try again.")
        
        st.markdown("---")
        st.info("""
        **Sample Login Credentials:**
        
        **HOD (Head of Department):**
        - Username: `admin`
        - Password: `admin123`
        
        **Class Teacher:**
        - Username: `classteacher`
        - Password: `teacher123`
        
        **Teacher:**
        - Username: `teacher`
        - Password: `teacher123`
        
        ⚠️ **Security Note:** Please change default passwords after first login!
        """)
        
        # Show role information
        with st.expander("ℹ️ About User Roles"):
            st.markdown("""
            **HOD (Head of Department):**
            - Full access to all features
            - Can manage users and students
            - Can view all reports and analytics
            - Can edit attendance records
            
            **Class Teacher:**
            - Can manage students
            - Can take attendance
            - Can view and export reports
            - Can edit attendance records
            
            **Teacher:**
            - Can take attendance
            - Can view class reports
            - Can view analytics
            """)

