import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import calendar

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="ENTC B.Tech B Facial Attendance System",
    page_icon="👨‍🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS styling
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card styling */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    
    /* Metrics styling */
    div.css-12w0qpk.e1tzin5v2 {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #1E3A8A;
    }
    
    /* Dashboard cards */
    .dashboard-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        margin-bottom: 1rem;
    }
    
    /* Success metrics */
    .success-metric {
        color: #1cc88a;
        font-weight: bold;
    }
    
    /* Warning metrics */
    .warning-metric {
        color: #f6c23e;
        font-weight: bold;
    }
    
    /* Danger metrics */
    .danger-metric {
        color: #e74a3b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

import os
import datetime
import traceback
from PIL import Image
import pandas as pd
import sqlite3
import requests
import logging
import io
import time
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calendar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

# Create necessary directories if they don't exist
os.makedirs("faces", exist_ok=True)
os.makedirs("excel_exports", exist_ok=True)
os.makedirs("db", exist_ok=True)

# Import database utilities with error handling
try:
    from utils.db_utils import (
        get_connection,
        init_db,
        register_student,
        get_all_students,
        get_subjects,
        mark_attendance,
        get_attendance_report,
        get_class_attendance_report,
        get_student_attendance_report,
        get_student_attendance_summary,
        get_student_details,
        get_class_attendance_summary,
        get_student_enrolled_subjects,
        update_student,
        delete_student,
        get_students_by_subject,
        enroll_all_students_in_all_subjects,
        enroll_student_in_all_subjects
    )
except ImportError as e:
    logger.error(f"Error importing database utilities: {str(e)}")
    st.error(f"Database utilities not found: {str(e)}")

# Try importing DeepFace with error handling
try:
    from utils.deepface_utils import (
        verify_faces,
        detect_faces_with_details,
        save_session_stats
    )
    deepface_available = True
except ImportError as e:
    logger.error(f"Error importing DeepFace: {str(e)}")
    deepface_available = False
    st.error(f"Error loading DeepFace module. Please check installation: {str(e)}")

# Try importing Google Sheets utilities
try:
    from utils.sheets_utils import (
        get_sheets_exporter,
        export_to_sheets,
        update_attendance_sheet,
        get_spreadsheet_info
    )
    sheets_available = True
except ImportError as e:
    logger.warning(f"Google Sheets utilities not available: {str(e)}")
    sheets_available = False

# Initialize the database
try:
    from config import DB_PATH
    logger.info(f"Database path: {DB_PATH}")
    logger.info(f"Database file exists: {os.path.exists(str(DB_PATH))}")
    
    init_db()
    
    # Verify database connection and show status
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]
        conn.close()
        logger.info(f"Database ready - Students: {student_count}, Subjects: {subject_count}, Attendance: {attendance_count}")
    except Exception as e:
        logger.warning(f"Could not verify database status: {str(e)}")
    
    # Auto-enroll all existing students in all subjects on startup
    try:
        enrolled_count = enroll_all_students_in_all_subjects()
        if enrolled_count > 0:
            logger.info(f"Auto-enrolled {enrolled_count} student-subject relationships on startup")
    except Exception as e:
        logger.error(f"Error auto-enrolling students on startup: {str(e)}")
        # Don't fail app startup if enrollment fails
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error("Failed to initialize database. Check logs for details.")
    st.error(f"Error: {str(e)}")

# Initialize session state for authentication (MUST be done before any other session state access)
# This prevents AttributeError when accessing session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "session_token" not in st.session_state:
    st.session_state.session_token = None
if "token_checked" not in st.session_state:
    st.session_state.token_checked = False

# Import authentication utilities
try:
    from utils.auth_utils import authenticate_user, has_permission, can_access_feature, ROLES
    from pages.login import show_login_page
    auth_available = True
except ImportError as e:
    logger.error(f"Error importing auth utilities: {str(e)}")
    auth_available = False

# Try to restore session from persistent token
# Check on every refresh if not authenticated
if not st.session_state.authenticated or not st.session_state.user:
    try:
        from utils.session_utils import get_session_token
        
        # Check if we have a session token
        token_to_check = None
        
        # First check session state (persists during browser session)
        if st.session_state.session_token:
            token_to_check = st.session_state.session_token
        else:
            # Check query params (set by JavaScript from localStorage)
            query_params = st.experimental_get_query_params()
            if '_token' in query_params:
                token_to_check = query_params['_token'][0]
                # Remove the token from URL after reading
                st.experimental_set_query_params()
            else:
                # If no token in query params, check localStorage via JavaScript
                # This will only run once per page load since query params persist the check
                restore_script = """
                <script>
                (function() {
                    const token = localStorage.getItem('attendance_session_token');
                    if (token) {
                        const url = new URL(window.location);
                        // Only add token if not already in URL to prevent loops
                        if (!url.searchParams.has('_token')) {
                            url.searchParams.set('_token', token);
                            window.history.replaceState({}, '', url);
                            // Trigger a reload to restore session
                            window.location.reload();
                        }
                    }
                })();
                </script>
                """
                st.components.v1.html(restore_script, height=0)
        
        if token_to_check:
            user_data = get_session_token(token_to_check)
            if user_data:
                st.session_state.user = user_data
                st.session_state.authenticated = True
                st.session_state.session_token = token_to_check
                st.session_state.token_checked = True
            else:
                # Token expired or invalid, clear it
                st.session_state.session_token = None
                st.session_state.token_checked = True
                # Clear from localStorage too
                clear_localStorage_script = """
                <script>
                localStorage.removeItem('attendance_session_token');
                </script>
                """
                st.components.v1.html(clear_localStorage_script, height=0)
        else:
            st.session_state.token_checked = True
            
    except Exception as e:
        logger.error(f"Error restoring session: {str(e)}")
        st.session_state.token_checked = True

# Check authentication - show login page if not authenticated
if not st.session_state.authenticated or not st.session_state.user:
    if auth_available:
        # Hide sidebar during login
        st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
        show_login_page()
        st.stop()
    else:
        st.error("Authentication system not available. Please check installation.")
        st.stop()

# User is authenticated - show main application
user = st.session_state.user

# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state.page = "Teacher Dashboard"

# Sidebar navigation with user info and logout
st.sidebar.title("Navigation")

# Display user information
st.sidebar.markdown("---")
st.sidebar.markdown(f"**👤 {user['name']}**")
st.sidebar.markdown(f"*{user['role']}*")
st.sidebar.markdown(f"Department: {user['department']}")

# Logout button
if st.sidebar.button("🚪 Logout", use_container_width=True, type="secondary"):
    # Clear session token if exists
    if st.session_state.session_token:
        try:
            from utils.session_utils import delete_session_token
            delete_session_token(st.session_state.session_token)
        except:
            pass
    
    # Clear from localStorage and query params
    clear_localStorage_script = """
    <script>
    localStorage.removeItem('attendance_session_token');
    // Clear query params
    const url = new URL(window.location);
    url.searchParams.delete('_token');
    window.history.replaceState({}, '', url);
    </script>
    """
    st.components.v1.html(clear_localStorage_script, height=0)
    
    # Clear query params in Streamlit
    st.experimental_set_query_params()
    
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.session_token = None
    st.session_state.token_checked = False
    st.experimental_rerun()

st.sidebar.markdown("---")

# Modern navigation with icons and better styling (role-based)
st.sidebar.markdown("### Main")
if st.sidebar.button("📊 Teacher Dashboard", key="nav_dashboard", use_container_width=True):
    st.session_state.page = "Teacher Dashboard"

# Student Management - Only for HOD and Class Teacher
if can_access_feature(user, 'manage_students'):
    if st.sidebar.button("👤 Student Registration", key="nav_registration", use_container_width=True):
        st.session_state.page = "Student Registration"
    if st.sidebar.button("✏️ Edit Students", key="nav_edit_students", use_container_width=True):
        st.session_state.page = "Edit Students"

# Take Attendance - Available to all roles
if can_access_feature(user, 'take_attendance'):
    if st.sidebar.button("📝 Take Attendance", key="nav_take_attendance", use_container_width=True):
        st.session_state.page = "Take Attendance"

st.sidebar.markdown("### Reports")
# Attendance Reports - Available to all roles
if can_access_feature(user, 'view_class_reports'):
    if st.sidebar.button("📊 Attendance Reports", key="nav_reports", use_container_width=True):
        st.session_state.page = "Attendance Reports"

    if st.sidebar.button("🏫 Class-wise Reports", key="nav_class_reports", use_container_width=True):
        st.session_state.page = "Class Reports"

# Edit Attendance - Only for HOD and Class Teacher
if can_access_feature(user, 'edit_attendance'):
    if st.sidebar.button("🔄 Edit Attendance", key="nav_edit_attendance", use_container_width=True):
        st.session_state.page = "Edit Attendance"

st.sidebar.markdown("### Analytics")
if can_access_feature(user, 'view_analytics'):
    if st.sidebar.button("👁️ Recognition Stats", key="nav_stats", use_container_width=True):
        st.session_state.page = "Recognition Stats"

# User Management - Only for HOD
if can_access_feature(user, 'manage_users'):
    st.sidebar.markdown("### Administration")
    if st.sidebar.button("👥 User Management", key="nav_user_management", use_container_width=True):
        st.session_state.page = "User Management"

# Student Management - Enroll All Students
if can_access_feature(user, 'manage_students'):
    st.sidebar.markdown("### Quick Actions")
    if st.sidebar.button("📚 Enroll All Students in All Subjects", key="nav_enroll_all", use_container_width=True):
        st.session_state.page = "Enroll All Students"

# Email Settings - Only for HOD
if can_access_feature(user, 'manage_users'):
    if st.sidebar.button("📧 Email Settings", key="nav_email_settings", use_container_width=True):
        st.session_state.page = "Email Settings"

# Get current page from session state
page = st.session_state.page

# Import configuration
try:
    from config import (
        DEPARTMENT, YEAR, DIVISION, SUBJECT_SHORT_NAMES,
        ESP32_DEFAULT_URL, ESP32_DEFAULT_USERNAME, ESP32_DEFAULT_PASSWORD,
        REQUEST_TIMEOUT
    )
    department = DEPARTMENT
    year = YEAR
    division = DIVISION
    subject_short_names = SUBJECT_SHORT_NAMES
except ImportError:
    # Fallback to hardcoded values if config not available
    department = "ENTC"
    year = "B.Tech"
    division = "B"
    subject_short_names = {
        "Fiber Optic Communication": "FOC",
        "Microwave Engineering": "ME",
        "Mobile Computing ": "MC",
        "E-Waste Management": "Ewaste",
        "Data Structures and Algorithms in Java": "DSAJ",
        "Engineering Economics and Financial Management": "EEFM",
        "Microwave Engineering Lab": "ME Lab",
        "Mini Project": "Mini project"
    }
    ESP32_DEFAULT_URL = "http://192.168.137.208:8080"
    ESP32_DEFAULT_USERNAME = "admin"
    ESP32_DEFAULT_PASSWORD = "admin"
    REQUEST_TIMEOUT = 10

# Import validators
try:
    from utils.validators import validate_esp32_url, validate_roll_number, validate_name, validate_email
except ImportError:
    # Fallback: create dummy validators if not available
    def validate_esp32_url(url): return (True, None)
    def validate_roll_number(roll_no): return (True, None)
    def validate_name(name): return (True, None)
    def validate_email(email): return (True, None)

# Helper function to check if a file is an uploaded file
def is_uploaded_file(file_obj):
    return hasattr(file_obj, 'name') and hasattr(file_obj, 'getvalue')

# Function to display recognition statistics
def display_recognition_stats(processing_time, detected_faces, recognized_students, confidence_scores, model_name="Unknown"):
    """Display recognition statistics in a visually appealing way"""
    st.subheader("📊 Recognition Statistics")
    
    cols = st.columns(5)
    with cols[0]:
        st.metric("Processing Time", f"{processing_time:.2f} sec")
    with cols[1]:
        st.metric("Faces Detected", f"{detected_faces}")
    with cols[2]:
        st.metric("Students Recognized", f"{len(recognized_students)}")
    with cols[3]:
        recognition_rate = (len(recognized_students) / detected_faces * 100) if detected_faces > 0 else 0
        st.metric("Recognition Rate", f"{recognition_rate:.1f}%")
    with cols[4]:
        st.metric("Model", model_name)
    
    # Display confidence information if available
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        st.metric("Average Confidence", f"{avg_confidence:.2f}")
        
        # Create a histogram of confidence scores
        if len(confidence_scores) > 1:
            hist_data = pd.DataFrame({'Confidence': confidence_scores})
            st.bar_chart(hist_data.Confidence.value_counts(bins=5, sort=False))

# Function to visualize face detection and recognition
def visualize_detected_faces(image_path, face_locations, recognized_students=None):
    """
    Create a visualization of the classroom image with bounding boxes 
    around detected faces, highlighting recognized students
    
    Args:
        image_path: Path to the classroom image
        face_locations: List of face location dictionaries with x, y, w, h
        recognized_students: List of recognized student dictionaries
    """
    try:
        import cv2
        
        # Load image with OpenCV
        image = cv2.imread(image_path)
        if image is None:
            st.error(f"Failed to load image for visualization: {image_path}")
            return
            
        # Convert to RGB for display
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create a copy for drawing
        display_image = image_rgb.copy()
        
        # Draw bounding boxes for all detected faces
        for i, face_loc in enumerate(face_locations):
            x = face_loc.get('x', 0)
            y = face_loc.get('y', 0)
            w = face_loc.get('w', 0)
            h = face_loc.get('h', 0)
            
            # Default color for unrecognized faces (red)
            color = (255, 0, 0)
            label = f"Face {i+1}"
            
            # Check if this face belongs to a recognized student
            if recognized_students:
                # This is a simplified matching approach
                # In a real implementation, you would map detected faces to recognized students
                if i < len(recognized_students):
                    # For recognized students, use green color
                    color = (0, 255, 0)
                    student = recognized_students[i]
                    label = f"{student['roll_no']}"
            
            # Draw rectangle
            cv2.rectangle(display_image, (x, y), (x+w, y+h), color, 2)
            
            # Draw label
            cv2.putText(
                display_image, 
                label, 
                (x, y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                color, 
                2
            )
        
        # Display the image with annotations (smaller size)
        st.subheader("Detected Faces")
        # Resize image to make it smaller
        height, width = display_image.shape[:2]
        scale = 0.5  # 50% of original size
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_image = cv2.resize(display_image, (new_width, new_height))
        st.image(resized_image, caption="Detected Faces", width=400)
        
    except Exception as e:
        logger.error(f"Error visualizing face detection: {str(e)}")
        st.error(f"Failed to create visualization: {str(e)}")

# Main page content
if page == "Teacher Dashboard":
    st.title("📊 Teacher Dashboard")
    st.markdown('<div class="dashboard-card"><p>View and manage student information for ENTC B.Tech b division.</p></div>', unsafe_allow_html=True)
    st.subheader(f"Department: {department} | Year: {year} | Division: {division}")
    
    # Get all students
    try:
        all_students = get_all_students()
        
        if not all_students:
            st.warning("⚠️ No students registered yet.")
            st.info("""
            **Get Started:**
            1. Click **👤 Student Registration** in the sidebar
            2. Add students with their photos and details
            3. Students will be automatically enrolled in all subjects
            
            **Database Check:**
            - Database location: `db/attendance.db`
            - If this is a fresh installation, the database will be created automatically
            - Check application logs if you encounter issues
            """)
            
            # Show database status
            try:
                from utils.db_utils import check_database_status
                db_status = check_database_status()
                
                with st.expander("🔍 Database Diagnostic Information", expanded=False):
                    st.write(f"**Database Path:** `{db_status['database_path']}`")
                    st.write(f"**Database Exists:** {'✅ Yes' if db_status['database_exists'] else '❌ No'}")
                    st.write(f"**Tables Exist:** {'✅ Yes' if db_status['tables_exist'] else '❌ No'}")
                    if db_status['tables_exist']:
                        st.write(f"**Tables:** {', '.join(db_status.get('tables', []))}")
                    st.write(f"**Students Count:** {db_status['students_count']}")
                    st.write(f"**Subjects Count:** {db_status['subjects_count']}")
                    st.write(f"**Attendance Records:** {db_status['attendance_count']}")
                    if db_status.get('error'):
                        st.error(f"**Error:** {db_status['error']}")
            except Exception as e:
                logger.error(f"Error checking database status: {str(e)}")
        else:
            # Convert to DataFrame for display
            students_df = pd.DataFrame([
                {
                    "ID": student["id"],
                    "Roll No": student["roll_no"],
                    "Name": student["name"],
                    "Email": student["email"] or "",
                    "Department": student["department"],
                    "Year": student["year"],
                    "Division": student["division"]
                }
                for student in all_students
            ])
            
            # Search functionality
            search_term = st.text_input("🔍 Search students by name or roll number:")
            
            if search_term:
                filtered_df = students_df[
                    students_df["Name"].str.contains(search_term, case=False) | 
                    students_df["Roll No"].str.contains(search_term, case=False)
                ]
            else:
                filtered_df = students_df
            
            # Display student statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Students", len(students_df))
            with col2:
                st.metric("Departments", len(students_df["Department"].unique()))
            with col3:
                st.metric("Divisions", len(students_df["Division"].unique()))
            
            # Display students table
            st.markdown("### Student List")
            st.dataframe(
                filtered_df.drop(columns=["ID"]), 
                use_container_width=True,
                hide_index=True
            )
            
            # Export functionality
            if st.button("Export Student List to Excel"):
                # Create Excel file
                excel_path = os.path.join("excel_exports", f"Students_{department}_{year}{division}.xlsx")
                try:
                    # Using context manager to ensure the file is properly closed
                    student_df_export = filtered_df.drop(columns=["ID"])
                    with pd.ExcelWriter(excel_path, mode='w') as writer:
                        student_df_export.to_excel(writer, index=False)
                    
                    with open(excel_path, "rb") as file:
                        st.download_button(
                            label="Download Excel File",
                            data=file,
                            file_name=f"Students_{department}_{year}{division}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    # Export to Google Sheets in parallel
                    if sheets_available:
                        try:
                            worksheet_name = f"Students_{department}_{year}{division}"
                            if export_to_sheets(student_df_export, worksheet_name):
                                sheets_info = get_spreadsheet_info()
                                if sheets_info and sheets_info.get('url'):
                                    st.success(f"✅ Student list exported to Google Sheets")
                                    st.info(f"📊 [Open Google Sheet]({sheets_info['url']})")
                                else:
                                    st.success(f"✅ Student list also exported to Google Sheets")
                            else:
                                logger.warning("Google Sheets export failed for student list, but Excel export succeeded")
                        except Exception as sheets_error:
                            logger.error(f"Error exporting student list to Google Sheets: {str(sheets_error)}")
                except Exception as e:
                    logger.error(f"Error exporting student list to Excel: {str(e)}")
                    st.error(f"Failed to export student list: {str(e)}")
            
            # Student details and editing option
            st.markdown("### Student Details")
            
            if not filtered_df.empty:
                selected_roll = st.selectbox(
                    "Select a student to view details:",
                    options=filtered_df["Roll No"].tolist(),
                    format_func=lambda x: f"{x} - {filtered_df[filtered_df['Roll No']==x]['Name'].values[0]}" if x else "Select a student"
                )
                
                if selected_roll:
                    try:
                        student_id = filtered_df[filtered_df["Roll No"] == selected_roll]["ID"].values[0]
                        selected_student = next((s for s in all_students if s["id"] == student_id), None)
                        
                        if selected_student:
                            cols = st.columns([1, 3])
                            
                            with cols[0]:
                                try:
                                    if os.path.exists(selected_student["image_path"]):
                                        img = Image.open(selected_student["image_path"])
                                        st.image(img, width=200, caption=f"{selected_roll}")
                                    else:
                                        st.warning("Student image file not found.")
                                except Exception as e:
                                    logger.error(f"Error loading student image: {str(e)}")
                                    st.warning("Unable to load student image.")
                            
                            with cols[1]:
                                st.markdown(f"### {selected_student['name']}")
                                st.markdown(f"**Roll No:** {selected_student['roll_no']}")
                                st.markdown(f"**Email:** {selected_student['email'] or 'N/A'}")
                                st.markdown(f"**Department:** {selected_student['department']}")
                                st.markdown(f"**Year:** {selected_student['year']}")
                                st.markdown(f"**Division:** {selected_student['division']}")
                                
                                # Get student's enrolled subjects
                                try:
                                    enrolled_subjects = get_student_enrolled_subjects(student_id)
                                    
                                    if enrolled_subjects:
                                        st.markdown("**Enrolled Subjects:**")
                                        
                                        # Display subjects as badges in a more modern way
                                        subject_badges = []
                                        for subject in enrolled_subjects:
                                            subject_code = subject['code']
                                            subject_name = subject['name']
                                            short_name = subject_short_names.get(subject_name, subject_code)
                                            subject_badges.append(f"<span style='display:inline-block; margin:2px; padding:4px 8px; background-color:#1E3A8A; color:white; border-radius:12px; font-size:0.8em;'>{short_name}</span>")
                                        
                                        st.markdown(f"<div>{''.join(subject_badges)}</div>", unsafe_allow_html=True)
                                        st.caption(f"Total subjects: {len(enrolled_subjects)}")
                                        
                                        # Add a section to show subject-wise attendance if available
                                        try:
                                            attendance_summary = get_student_attendance_summary(student_id)
                                            if attendance_summary:
                                                st.markdown("**Attendance Overview:**")
                                                
                                                # Calculate overall attendance
                                                total_present = sum(row["present_count"] for row in attendance_summary)
                                                total_classes = sum(row["total_classes"] for row in attendance_summary)
                                                overall_percentage = round(total_present / total_classes * 100, 1) if total_classes > 0 else 0
                                                
                                                # Display overall attendance with appropriate color
                                                color = "#4caf50" if overall_percentage >= 75 else "#ff9800" if overall_percentage >= 50 else "#f44336"
                                                st.markdown(f"<div style='font-weight:bold'>Overall Attendance: <span style='color:{color}'>{overall_percentage}%</span></div>", unsafe_allow_html=True)
                                                
                                        except Exception as att_e:
                                            logger.error(f"Error retrieving attendance summary: {str(att_e)}")
                                            # Just skip attendance display if there's an error
                                            pass
                                    else:
                                        # Only show this message if user has permission to manage students
                                        if can_access_feature(user, 'manage_students'):
                                            st.info("ℹ️ **Note:** This student is not enrolled in any subjects yet.")
                                            st.markdown("💡 **To enroll this student:** Go to **✏️ Edit Students** page or use **👤 Student Registration** to update their enrollment.")
                                            
                                            # Show available subjects for reference
                                            try:
                                                all_subjects = get_subjects()
                                                if all_subjects:
                                                    st.markdown("**Available subjects in database:**")
                                                    subject_list = ", ".join([f"{s[1]} ({s[2]})" for s in all_subjects])
                                                    st.caption(subject_list)
                                            except:
                                                pass
                                        else:
                                            # For teachers without edit permissions, just show a simple note
                                            st.info("ℹ️ This student is not enrolled in any subjects.")
                                except Exception as e:
                                    logger.error(f"Error retrieving enrolled subjects: {str(e)}\n{traceback.format_exc()}")
                                    st.error(f"Failed to retrieve enrolled subjects: {str(e)}")
                        else:
                            st.error("Student details not found in database.")
                    except Exception as e:
                        logger.error(f"Error retrieving student details: {str(e)}")
                        st.error(f"Failed to retrieve student details. Error: {str(e)}")
            else:
                st.info("No students match your search criteria.")
    
    except Exception as e:
        logger.error(f"Error loading student data: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error: {str(e)}")

elif page == "User Management":
    # Only HOD can access user management
    if not can_access_feature(user, 'manage_users'):
        st.error("❌ Access Denied: You do not have permission to access User Management.")
        st.info("Only HOD (Head of Department) can manage users.")
    else:
        st.title("👥 User Management")
        st.markdown("---")
        
        try:
            from utils.auth_utils import get_all_users, create_user, update_user_password, ROLES
            
            # Tabs for different management functions
            tab1, tab2, tab3 = st.tabs(["View Users", "Create User", "Change Password"])
            
            with tab1:
                st.subheader("All Users")
                users = get_all_users()
                
                if users:
                    # Display users in a table
                    user_data = []
                    for u in users:
                        user_data.append({
                            'ID': u['id'],
                            'Username': u['username'],
                            'Name': u['name'],
                            'Role': u['role'],
                            'Email': u['email'] or 'N/A',
                            'Department': u['department'],
                            'Status': 'Active' if u['is_active'] else 'Inactive',
                            'Last Login': u['last_login'] or 'Never',
                            'Created': u['created_at']
                        })
                    
                    df = pd.DataFrame(user_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Users", len(users))
                    with col2:
                        hod_count = sum(1 for u in users if u['role'] == 'HOD')
                        st.metric("HOD", hod_count)
                    with col3:
                        ct_count = sum(1 for u in users if u['role'] == 'Class Teacher')
                        st.metric("Class Teachers", ct_count)
                    with col4:
                        t_count = sum(1 for u in users if u['role'] == 'Teacher')
                        st.metric("Teachers", t_count)
                else:
                    st.info("No users found.")
            
            with tab2:
                st.subheader("Create New User")
                with st.form("create_user_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_username = st.text_input("Username *", help="Must be unique")
                        new_name = st.text_input("Full Name *")
                        new_email = st.text_input("Email")
                    with col2:
                        new_role = st.selectbox("Role *", options=list(ROLES.keys()), 
                                               format_func=lambda x: ROLES[x]['name'])
                        new_department = st.text_input("Department", value=user['department'])
                        new_password = st.text_input("Password *", type="password", 
                                                    help="Minimum 6 characters recommended")
                    
                    create_button = st.form_submit_button("Create User", type="primary")
                    
                    if create_button:
                        if not all([new_username, new_name, new_role, new_password]):
                            st.error("⚠️ Please fill in all required fields (marked with *)")
                        elif len(new_password) < 6:
                            st.error("⚠️ Password must be at least 6 characters long")
                        else:
                            success, error_msg = create_user(
                                new_username, new_password, new_role, 
                                new_name, new_email, new_department
                            )
                            if success:
                                st.success(f"✅ User '{new_username}' created successfully!")
                                st.experimental_rerun()
                            else:
                                st.error(f"❌ {error_msg}")
            
            with tab3:
                st.subheader("Change Password")
                st.info("Select a user and enter their current and new password.")
                
                users_list = get_all_users()
                if users_list:
                    user_options = {f"{u['username']} ({u['name']})": u['id'] for u in users_list}
                    selected_user_display = st.selectbox("Select User", options=list(user_options.keys()))
                    selected_user_id = user_options[selected_user_display]
                    
                    with st.form("change_password_form"):
                        old_password = st.text_input("Current Password", type="password")
                        new_password = st.text_input("New Password", type="password")
                        confirm_password = st.text_input("Confirm New Password", type="password")
                        
                        change_button = st.form_submit_button("Change Password", type="primary")
                        
                        if change_button:
                            if not all([old_password, new_password, confirm_password]):
                                st.error("⚠️ Please fill in all fields")
                            elif new_password != confirm_password:
                                st.error("⚠️ New passwords do not match")
                            elif len(new_password) < 6:
                                st.error("⚠️ New password must be at least 6 characters long")
                            else:
                                success, error_msg = update_user_password(
                                    selected_user_id, old_password, new_password
                                )
                                if success:
                                    st.success("✅ Password changed successfully!")
                                else:
                                    st.error(f"❌ {error_msg}")
                else:
                    st.info("No users found.")
                    
        except Exception as e:
            logger.error(f"Error in User Management: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Error: {str(e)}")

elif page == "Student Registration":
    # Check permission
    if not can_access_feature(user, 'manage_students'):
        st.error("❌ Access Denied: You do not have permission to register students.")
        st.info("Only HOD and Class Teachers can register students.")
    else:
        st.title("👤 Student Registration")
    
    with st.form("student_registration"):
        name = st.text_input("Full Name")
        roll_no = st.text_input("Roll Number (e.g., EC4201)")
        email = st.text_input("Email Address")
        
        # Fixed fields
        st.text(f"Department: {department}")
        st.text(f"Year: {year}")
        st.text(f"Division: {division}")
        
        # Subject selection
        try:
            subjects = get_subjects()
            subject_options = [subject[1] for subject in subjects]  # Use code instead of full name
            
            # Subject enrollment - default to all subjects
            st.subheader("Subject Enrollment")
            select_all = st.checkbox("Select All Subjects", value=True, help="By default, students are enrolled in all subjects")
            
            if select_all:
                selected_subjects = subject_options
                st.info(f"✅ All {len(subject_options)} subjects will be selected by default")
                # Show the list of selected subjects for clarity
                st.write("**Enrolled in:**", ", ".join(selected_subjects))
            else:
                selected_subjects = st.multiselect("Select Enrolled Subjects", subject_options, default=subject_options, help="You can deselect specific subjects if needed")
                
        except Exception as e:
            logger.error(f"Error loading subjects: {str(e)}")
            st.error("Failed to load subjects. Please check database connection.")
            subjects = []
            selected_subjects = []
            select_all = True  # Default to True even on error
        
        # Face image upload
        face_image = st.file_uploader("Upload Face Image", type=["jpg", "jpeg", "png"])
        
        # Preview image if uploaded
        if face_image is not None:
            try:
                st.image(face_image, caption="Student Face", width=200)
            except Exception as e:
                logger.error(f"Error displaying face image: {str(e)}")
                st.error("Failed to display image preview.")
        
        submitted = st.form_submit_button("Register Student")
        
        if submitted:
            if not name or not roll_no or not face_image:
                st.error("Name, Roll Number, and Face Image are required fields")
            else:
                try:
                    # If no subjects selected, default to all subjects
                    if not selected_subjects and subjects:
                        selected_subjects = subject_options
                        subject_ids = [subject[0] for subject in subjects]
                        st.info("ℹ️ No subjects selected. Enrolling in all subjects by default.")
                    elif selected_subjects:
                        # Get subject IDs from selected subject names
                        subject_ids = [subject[0] for subject in subjects if subject[1] in selected_subjects]
                    else:
                        st.error("No subjects available. Please check database configuration.")
                        subject_ids = []
                    
                    if subject_ids:
                        # Save face image
                        image_path = os.path.join("faces", f"{roll_no}.jpg")
                        with open(image_path, "wb") as f:
                            f.write(face_image.getvalue())
                        
                        # Register student in database
                        student_id = register_student(roll_no, name, department, year, division, image_path, subject_ids, email)
                        
                        if student_id:
                            st.success(f"✅ Student {name} registered successfully!")
                            st.success(f"📚 Enrolled in {len(subject_ids)} subject(s)")
                        else:
                            st.error("Failed to register student. Roll number may already exist.")
                    else:
                        st.error("Cannot register student without subjects. Please check database.")
                except Exception as e:
                    logger.error(f"Error registering student: {str(e)}")
                    st.error(f"Error registering student: {str(e)}")

elif page == "Edit Students":
    # Check permission
    if not can_access_feature(user, 'manage_students'):
        st.error("❌ Access Denied: You do not have permission to edit students.")
        st.info("Only HOD and Class Teachers can edit students.")
    else:
        st.title("✏️ Edit Students")
        st.markdown("---")
        
        try:
            # Get all students
            students = get_all_students()
            
            if not students:
                st.info("No students found in the database.")
            else:
                # Student selection
                student_options = {f"{s['roll_no']} - {s['name']}": s['id'] for s in students}
                selected_student_display = st.selectbox(
                    "Select Student to Edit",
                    options=list(student_options.keys()),
                    key="edit_student_select"
                )
                selected_student_id = student_options[selected_student_display]
                
                # Get student details
                student_details = get_student_details(selected_student_id)
                enrolled_subjects = get_student_enrolled_subjects(selected_student_id)
                enrolled_subject_ids = [s['id'] for s in enrolled_subjects]
                
                if student_details:
                    st.markdown("---")
                    st.subheader("Edit Student Information")
                    
                    with st.form("edit_student_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_roll_no = st.text_input("Roll Number", value=student_details['roll_no'])
                            new_name = st.text_input("Full Name", value=student_details['name'])
                            new_email = st.text_input("Email Address", value=student_details['email'] or '')
                        
                        with col2:
                            st.text(f"Department: {student_details['department']}")
                            st.text(f"Year: {student_details['year']}")
                            st.text(f"Division: {student_details['division']}")
                        
                        # Subject enrollment
                        st.subheader("Subject Enrollment")
                        try:
                            all_subjects = get_subjects()
                            subject_options = {f"{s[1]} ({s[2]})": s[0] for s in all_subjects}
                            
                            # Pre-select enrolled subjects
                            selected_subject_ids = st.multiselect(
                                "Select Enrolled Subjects",
                                options=list(subject_options.values()),
                                default=enrolled_subject_ids,
                                format_func=lambda x: next((f"{s[1]} ({s[2]})" for s in all_subjects if s[0] == x), str(x))
                            )
                        except Exception as e:
                            logger.error(f"Error loading subjects: {str(e)}")
                            st.error("Failed to load subjects.")
                            selected_subject_ids = enrolled_subject_ids
                        
                        # Image update
                        st.subheader("Update Face Image (Optional)")
                        new_face_image = st.file_uploader(
                            "Upload New Face Image",
                            type=["jpg", "jpeg", "png"],
                            help="Leave empty to keep current image"
                        )
                        
                        if new_face_image is not None:
                            try:
                                st.image(new_face_image, caption="New Face Image", width=200)
                            except Exception as e:
                                logger.error(f"Error displaying image: {str(e)}")
                        
                        # Action buttons
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            update_button = st.form_submit_button("💾 Update Student", type="primary", use_container_width=True)
                        with col_btn2:
                            delete_button = st.form_submit_button("🗑️ Delete Student", use_container_width=True)
                        with col_btn3:
                            cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
                        
                        if update_button:
                            try:
                                # Validate inputs
                                if not new_roll_no or not new_name:
                                    st.error("⚠️ Roll number and name are required fields.")
                                else:
                                    # Handle image update
                                    new_image_path = None
                                    if new_face_image is not None:
                                        new_image_path = os.path.join("faces", f"{new_roll_no}.jpg")
                                        with open(new_image_path, "wb") as f:
                                            f.write(new_face_image.getvalue())
                                    
                                    # Update student
                                    success = update_student(
                                        student_id=selected_student_id,
                                        roll_no=new_roll_no,
                                        name=new_name,
                                        email=new_email if new_email else None,
                                        image_path=new_image_path,
                                        subject_ids=selected_subject_ids
                                    )
                                    
                                    if success:
                                        st.success(f"✅ Student {new_name} updated successfully!")
                                        st.experimental_rerun()
                                    else:
                                        st.error("❌ Failed to update student. Roll number may already be in use.")
                            except Exception as e:
                                logger.error(f"Error updating student: {str(e)}\n{traceback.format_exc()}")
                                st.error(f"Error updating student: {str(e)}")
                        
                        if delete_button:
                            # Show confirmation
                            st.warning("⚠️ Are you sure you want to delete this student? This action cannot be undone!")
                            confirm_delete = st.checkbox("I confirm I want to delete this student")
                            
                            if confirm_delete:
                                try:
                                    if delete_student(selected_student_id):
                                        st.success("✅ Student deleted successfully!")
                                        st.experimental_rerun()
                                    else:
                                        st.error("❌ Failed to delete student.")
                                except Exception as e:
                                    logger.error(f"Error deleting student: {str(e)}\n{traceback.format_exc()}")
                                    st.error(f"Error deleting student: {str(e)}")
                else:
                    st.error("Student details not found.")
                    
        except Exception as e:
            logger.error(f"Error in Edit Students page: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Error: {str(e)}")

elif page == "Enroll All Students":
    # Check permission
    if not can_access_feature(user, 'manage_students'):
        st.error("❌ Access Denied: You do not have permission to enroll students.")
        st.info("Only HOD and Class Teachers can enroll students.")
    else:
        st.title("📚 Enroll All Students in All Subjects")
        st.markdown("---")
        st.info("""
        **What this does:**
        - Enrolls all existing students in all available subjects
        - Only creates new enrollments (won't duplicate existing ones)
        - Safe to run multiple times
        """)
        
        try:
            # Get counts
            all_students = get_all_students()
            all_subjects = get_subjects()
            
            if not all_students:
                st.warning("⚠️ No students found in the database.")
                st.info("""
                **To add students:**
                1. Go to **👤 Student Registration** page in the sidebar
                2. Fill in student details and upload their photo
                3. Students will be automatically enrolled in all subjects
                
                **Database Status:**
                - Check if database is initialized properly
                - Verify database file exists at: `db/attendance.db`
                - Check application logs for database errors
                """)
            elif not all_subjects:
                st.warning("No subjects found in the database.")
            else:
                st.markdown("### Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Students", len(all_students))
                with col2:
                    st.metric("Total Subjects", len(all_subjects))
                with col3:
                    st.metric("Potential Enrollments", len(all_students) * len(all_subjects))
                
                st.markdown("---")
                
                if st.button("🚀 Enroll All Students in All Subjects", type="primary", use_container_width=True):
                    with st.spinner("Enrolling students in subjects..."):
                        enrolled_count = enroll_all_students_in_all_subjects()
                        
                        if enrolled_count > 0:
                            st.success(f"✅ Successfully created {enrolled_count} enrollments!")
                            st.info(f"All {len(all_students)} students are now enrolled in all {len(all_subjects)} subjects.")
                            st.experimental_rerun()
                        else:
                            st.info("ℹ️ All students are already enrolled in all subjects, or no enrollments were needed.")
                
                # Show current enrollment status
                st.markdown("---")
                st.markdown("### Current Enrollment Status")
                
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    # Get enrollment statistics
                    cursor.execute('''
                        SELECT 
                            s.id,
                            s.roll_no,
                            s.name,
                            COUNT(ss.subject_id) as enrolled_count
                        FROM students s
                        LEFT JOIN student_subjects ss ON s.id = ss.student_id
                        GROUP BY s.id
                        ORDER BY s.roll_no
                    ''')
                    
                    enrollment_data = []
                    for row in cursor.fetchall():
                        enrollment_data.append({
                            'Roll No': row['roll_no'],
                            'Name': row['name'],
                            'Enrolled Subjects': row['enrolled_count'],
                            'Status': '✅ Complete' if row['enrolled_count'] == len(all_subjects) else '⚠️ Incomplete'
                        })
                    
                    conn.close()
                    
                    if enrollment_data:
                        enrollment_df = pd.DataFrame(enrollment_data)
                        st.dataframe(enrollment_df, use_container_width=True, hide_index=True)
                        
                        # Summary
                        complete = sum(1 for e in enrollment_data if e['Status'] == '✅ Complete')
                        incomplete = len(enrollment_data) - complete
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Fully Enrolled", complete)
                        with col2:
                            st.metric("Needs Enrollment", incomplete)
                except Exception as e:
                    logger.error(f"Error getting enrollment status: {str(e)}")
                    st.error(f"Error retrieving enrollment status: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in Enroll All Students page: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Error: {str(e)}")

elif page == "Take Attendance":
    # Check permission
    if not can_access_feature(user, 'take_attendance'):
        st.error("❌ Access Denied: You do not have permission to take attendance.")
    else:
        st.title("📝 Take Attendance")
    st.markdown('<div class="dashboard-card"><p>Capture attendance using facial recognition.</p></div>', unsafe_allow_html=True)
    st.subheader(f"Department: {department} | Year: {year} | Division: {division}")
    
    # Check if we need to show success message from previous submission
    if hasattr(st.session_state, 'last_attendance') and st.session_state.get('clear_attendance_form', False):
        last = st.session_state.last_attendance
        st.success(f"✅ Successfully saved attendance for {last['count']} students in {last['subject']} on {last['date']} ({last['period']}).")
        
        # Clear the flag so the message doesn't show again on manual refresh
        st.session_state.clear_attendance_form = False
        
        # Reset form fields
        if 'form_key' in st.session_state:
            del st.session_state['form_key']
        
        # Clear uploaded files
        if 'uploaded_files' in st.session_state:
            del st.session_state['uploaded_files']
        
        # Add a button to take new attendance
        if st.button("Take Another Attendance", key="take_another"):
            # This will be handled in the next rerun - just clear the session state
            pass
    
    # Create columns for form inputs
    col1, col2 = st.columns(2)
    
    # Get subjects from database with error handling
    try:
        subjects = get_subjects()
        subject_options = [subject[1] for subject in subjects]  # Use code instead of full name
        
        with col1:
            if subject_options:
                selected_subject = st.selectbox("Select Subject", subject_options)
                subject_id = next((subject[0] for subject in subjects if subject[1] == selected_subject), None)
            else:
                st.warning("No subjects found in database. Please check database configuration.")
                selected_subject = None
                subject_id = None
        
        with col2:
            periods = [
                "10:15 - 11:15",
                "11:15 - 12:15",
                "01:15 - 02:15",
                "02:15 - 03:15",
                "03:30 - 04:30",
                "04:30 - 05:30"
            ]
            selected_period = st.selectbox("Select Period", periods)
        
        # Add date selection
        attendance_date = st.date_input("Select Date", value=datetime.date.today())
        
    except Exception as e:
        logger.error(f"Error retrieving subjects: {str(e)}")
        st.error("Failed to retrieve subjects from database.")
        subjects = []
        subject_options = []
        attendance_date = datetime.date.today()
    
    st.divider()
    
    # Image input section
    st.subheader("Classroom Image")
    image_source = st.radio(
        "Image Source",
        ["Upload Image", "Capture from ESP32-CAM", "Use Webcam"],
        horizontal=True
    )
    
    # Add model selection options
    st.subheader("Recognition Settings")
    
    # Accuracy tips
    with st.expander("💡 Tips for Maximum Accuracy", expanded=False):
        st.markdown("""
        **Best Configuration for Maximum Accuracy:**
        - **Model:** ArcFace (99%+ accuracy) or Facenet512 (99% accuracy)
        - **Detector:** MTCNN (best) or RetinaFace (very good)
        - **Threshold:** 0.3-0.4 (lower = stricter, fewer false positives)
        
        **Quick Setup:**
        1. Select **ArcFace** model + **MTCNN** detector
        2. Set threshold to **0.4**
        3. Use high-quality student photos (see guide)
        4. Ensure good classroom lighting
        
        📖 See `ACCURACY_GUIDE.md` for detailed recommendations.
        """)
    
    cols = st.columns([2, 1, 1])
    with cols[0]:
        model_name = st.selectbox(
            "Face Recognition Model",
            ["ArcFace", "Facenet512", "VGG-Face", "SFace", "OpenFace", "DeepFace"],
            index=0,  # Default to ArcFace (highest accuracy). Facenet512 is at index 1 if ArcFace not available
            help="ArcFace: Highest accuracy (~99%). Facenet512: Very high accuracy (~99%), good balance. See ACCURACY_GUIDE.md for details."
        )

    with cols[1]:
        threshold = st.slider(
            "Matching Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.4,
            step=0.05,
            help="Lower = stricter (fewer false positives). Recommended: 0.3-0.4 for high accuracy"
        )
    
    with cols[2]:
        detector_backend = st.selectbox(
            "Face Detector",
            ["opencv", "mtcnn", "retinaface", "ssd", "dlib"],
            index=0,
            help="MTCNN: Highest accuracy (slower). RetinaFace: Very accurate. OpenCV: Fast (default)"
        )
    
    image_files = []
    if image_source == "Upload Image":
        allow_multiple = st.checkbox("Upload multiple images", value=False, 
                                    help="Enable to upload multiple classroom images at once")
        
        if allow_multiple:
            # Multiple image upload
            uploaded_files = st.file_uploader("Upload classroom images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="multi_image_uploader")
            
            if uploaded_files:
                image_files = uploaded_files
                # Display image previews
                st.subheader("Uploaded Images")
                preview_cols = st.columns(min(len(uploaded_files), 3))
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        with preview_cols[i % 3]:
                            image = Image.open(uploaded_file)
                            st.image(image, caption=f"Image {i+1}", width=200)
                    except Exception as e:
                        st.error(f"Error opening image {i+1}: {str(e)}")
                
                # Select which image to process
                if len(uploaded_files) > 1:
                    selected_image_index = st.selectbox(
                        "Select which image to process", 
                        range(len(uploaded_files)), 
                        format_func=lambda i: f"Image {i+1}"
                    )
                    image_file = uploaded_files[selected_image_index]
                else:
                    image_file = uploaded_files[0]
                    
                # Add button to process all images
                process_all = st.checkbox("Process all images", value=False,
                                         help="Enable to analyze all uploaded images in sequence")
        else:
            # Single image upload (original behavior)
            image_file = st.file_uploader("Upload classroom image", type=["jpg", "jpeg", "png"], key="single_image_uploader")
            image_files = [image_file] if image_file is not None else []
            process_all = False
            
            if image_file is not None:
                try:
                    # Display uploaded image
                    image = Image.open(image_file)
                    st.image(image, caption="Uploaded Image", width=400)
                except Exception as e:
                    logger.error(f"Error opening uploaded image: {str(e)}")
                    st.error("Failed to open uploaded image. Please try a different file.")
    elif image_source == "Use Webcam":
        st.info("Webcam capture will use your browser's camera. Please grant permission if prompted.")
        
        # Camera input for webcam capture
        webcam_image = st.camera_input("Take a picture from webcam")
        
        if webcam_image is not None:
            # Add webcam image to image_files list
            image_files = [webcam_image]
            image_file = webcam_image
            process_all = False
            
            try:
                # Display captured image
                image = Image.open(webcam_image)
                st.image(image, caption="Captured Image", width=400)
            except Exception as e:
                logger.error(f"Error opening webcam image: {str(e)}")
                st.error("Failed to process webcam image.")
    else:
        # ESP32-CAM Configuration
        st.info("💡 Enter your ESP32-CAM IP address and credentials (if required)")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            esp32_base_url = st.text_input(
                "ESP32-CAM Base URL", 
                value=ESP32_DEFAULT_URL,
                help="Enter the base URL of your ESP32-CAM including port if needed (e.g., http://192.168.137.208:8080)"
            )
            # Validate URL
            if esp32_base_url:
                is_valid, error_msg = validate_esp32_url(esp32_base_url)
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                elif error_msg and "Warning" in error_msg:
                    st.warning(error_msg)
        
        with col2:
            use_auth = st.checkbox("Use Authentication", value=True, help="Enable if your ESP32-CAM requires login")
        
        esp32_username = None
        esp32_password = None
        if use_auth:
            auth_col1, auth_col2 = st.columns(2)
            with auth_col1:
                esp32_username = st.text_input("Username", value=ESP32_DEFAULT_USERNAME, help="ESP32-CAM username")
            with auth_col2:
                esp32_password = st.text_input("Password", type="password", value=ESP32_DEFAULT_PASSWORD, help="ESP32-CAM password")
        
        # Build URLs
        stream_url = f"{esp32_base_url}/stream"
        capture_url = f"{esp32_base_url}/capture"
        
        # Create authentication if needed
        auth = None
        if use_auth and esp32_username and esp32_password:
            from requests.auth import HTTPBasicAuth
            auth = HTTPBasicAuth(esp32_username, esp32_password)
        
        # Display live stream
        st.subheader("Live Stream")
        
        # SECURITY FIX: Do not embed credentials in URL (security risk)
        # For authenticated streams, we'll use a note instead
        if use_auth and esp32_username and esp32_password:
            st.warning("⚠️ **Security Note**: Live stream display with authentication may not work directly in the browser. Use the 'Capture Image' button to take snapshots instead.")
            # Show stream URL without credentials for reference
            st.info(f"Stream URL: `{stream_url}` (authentication required)")
            stream_display_url = stream_url
        else:
            stream_display_url = stream_url
        
        # Display stream using HTML - works with MJPEG streams
        # Note: For authenticated streams, browser may block the request
        stream_html = f"""
        <div style="text-align: center; margin: 20px 0;">
            <img src="{stream_display_url}" 
                 style="max-width: 100%; max-height: 500px; height: auto; border: 2px solid #ddd; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" 
                 alt="ESP32-CAM Stream"
                 onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'400\\' height=\\'300\\'%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\'%3EStream not available%3C/text%3E%3C/svg%3E';">
        </div>
        """
        st.markdown(stream_html, unsafe_allow_html=True)
        st.caption("💡 Live stream from ESP32-CAM. Click 'Capture Image' below to take a snapshot for attendance.")
        
        # Capture button
        col_cap1, col_cap2 = st.columns([1, 3])
        with col_cap1:
            capture_button = st.button("📸 Capture Image", type="primary", use_container_width=True)
        
        if capture_button:
            try:
                with st.spinner("Capturing image from ESP32-CAM..."):
                    # Try capture endpoint first
                    response = requests.get(capture_url, auth=auth, timeout=REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        # Save the captured image
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_path = f"captured_{timestamp}.jpg"
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        
                        image = Image.open(image_path)
                        st.success("✅ Image captured successfully!")
                        st.image(image, caption="Captured Image from ESP32-CAM", width=600)
                        image_file = image_path
                        image_files = [image_path]
                    elif response.status_code == 401:
                        st.error("❌ Authentication failed. Please check your username and password.")
                        logger.error(f"ESP32-CAM authentication failed. Status code: {response.status_code}")
                    else:
                        # Try alternative endpoints
                        alt_urls = [
                            f"{esp32_base_url}/jpg",
                            f"{esp32_base_url}/",
                            f"{esp32_base_url}/snapshot"
                        ]
                        captured = False
                        for alt_url in alt_urls:
                            try:
                                alt_response = requests.get(alt_url, auth=auth, timeout=REQUEST_TIMEOUT)
                                if alt_response.status_code == 200 and alt_response.headers.get('content-type', '').startswith('image'):
                                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                    image_path = f"captured_{timestamp}.jpg"
                                    with open(image_path, "wb") as f:
                                        f.write(alt_response.content)
                                    
                                    image = Image.open(image_path)
                                    st.success(f"✅ Image captured from {alt_url}!")
                                    st.image(image, caption="Captured Image from ESP32-CAM", width=600)
                                    image_file = image_path
                                    image_files = [image_path]
                                    captured = True
                                    break
                            except:
                                continue
                        
                        if not captured:
                            st.error(f"❌ Failed to capture image. Status code: {response.status_code}")
                            st.info("💡 Try different endpoints or check if authentication is required.")
                            logger.error(f"ESP32-CAM capture failed. Status code: {response.status_code}")
                            
            except requests.exceptions.Timeout:
                st.error("⏱️ Connection timeout. Please check if ESP32-CAM is accessible.")
                logger.error("ESP32-CAM connection timeout")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Connection error. Please verify the ESP32-CAM IP address and network connection.")
                logger.error("ESP32-CAM connection error")
            except requests.RequestException as e:
                logger.error(f"ESP32-CAM connection error: {str(e)}")
                st.error(f"❌ Error connecting to ESP32-CAM: {str(e)}")
            except Exception as e:
                logger.error(f"Error capturing image: {str(e)}")
                st.error(f"❌ Error: {str(e)}")
    
    # Check for form submissions first (outside button conditional)
    # This ensures form submission works even after rerun
    batch_form_submitted = st.session_state.get('batch_attendance_form_submitted', False)
    single_form_submitted = st.session_state.get('attendance_form_submitted', False)
    
    # Process form submissions outside of button conditional
    if batch_form_submitted and 'batch_attendance_data' in st.session_state:
        try:
            logger.info("🔔 BATCH FORM SUBMITTED - Processing attendance marking")
            form_data = st.session_state.batch_attendance_data
            selected_students = form_data['selected_students']
            subject_id_val = form_data['subject_id']
            selected_subject = form_data['selected_subject']
            selected_date = form_data['selected_date']
            selected_period = form_data['selected_period']
            all_enrolled_students = form_data['all_enrolled_students']
            
            logger.info(f"Form data retrieved: {len(selected_students)} students, subject_id={subject_id_val}, date={selected_date}")
            
            # Get selected student IDs
            marked_ids = [student_id for student_id, selected in selected_students.items() if selected]
            
            logger.info(f"Marked IDs: {marked_ids}")
            
            if subject_id_val is None:
                st.error("❌ Error: Subject ID is not available.")
                logger.error("Subject ID is None when trying to mark attendance")
            else:
                success_count = 0
                absent_count = 0
                
                logger.info(f"Processing batch attendance: {len(marked_ids)} students. Subject: {subject_id_val}, Date: {selected_date}, Period: {selected_period}")
                
                # Mark present students
                if marked_ids:
                    for student_id in marked_ids:
                        try:
                            success = mark_attendance(student_id, subject_id_val, selected_date, selected_period, status="present")
                            if success:
                                success_count += 1
                        except Exception as e:
                            logger.error(f"Error marking attendance for student_id={student_id}: {str(e)}")
                
                # Mark absent students
                all_enrolled_ids = [s["id"] for s in all_enrolled_students]
                absent_student_ids = [sid for sid in all_enrolled_ids if sid not in marked_ids]
                
                if absent_student_ids:
                    for student_id in absent_student_ids:
                        try:
                            success = mark_attendance(student_id, subject_id_val, selected_date, selected_period, status="absent")
                            if success:
                                absent_count += 1
                        except Exception as e:
                            logger.error(f"Error marking absent attendance for student_id={student_id}: {str(e)}")
                
                if success_count > 0 or absent_count > 0:
                    message = f"✅ Attendance saved for {success_count} present students"
                    if absent_count > 0:
                        message += f" and {absent_count} absent students"
                    message += f" on {selected_date}!"
                    st.success(message)
                    
                    st.session_state.last_attendance = {
                        'subject': selected_subject,
                        'date': selected_date,
                        'period': selected_period,
                        'count': success_count
                    }
                    
                    # Clear form submission state
                    st.session_state.batch_attendance_form_submitted = False
                    del st.session_state.batch_attendance_data
                    st.session_state.clear_attendance_form = True
                    st.rerun()
        except Exception as e:
            logger.error(f"Error processing batch attendance form: {str(e)}\n{traceback.format_exc()}")
            st.error(f"❌ Error marking attendance: {str(e)}")
            st.session_state.batch_attendance_form_submitted = False
    
    if single_form_submitted and 'attendance_data' in st.session_state:
        try:
            logger.info("🔔 SINGLE FORM SUBMITTED - Processing attendance marking")
            form_data = st.session_state.attendance_data
            selected_students = form_data['selected_students']
            subject_id_val = form_data['subject_id']
            selected_subject = form_data['selected_subject']
            selected_date = form_data['selected_date']
            selected_period = form_data['selected_period']
            all_enrolled_students = form_data['all_enrolled_students']
            
            logger.info(f"Form data retrieved: {len(selected_students)} students, subject_id={subject_id_val}, date={selected_date}")
            
            # Get selected student IDs
            marked_ids = [student_id for student_id, selected in selected_students.items() if selected]
            
            logger.info(f"Marked IDs: {marked_ids}")
            
            if subject_id_val is None:
                st.error("❌ Error: Subject ID is not available.")
                logger.error("Subject ID is None when trying to mark attendance")
            else:
                success_count = 0
                absent_count = 0
                
                logger.info(f"Processing attendance: {len(marked_ids)} students. Subject: {subject_id_val}, Date: {selected_date}, Period: {selected_period}")
                
                # Mark present students
                if marked_ids:
                    for student_id in marked_ids:
                        try:
                            success = mark_attendance(student_id, subject_id_val, selected_date, selected_period, status="present")
                            if success:
                                success_count += 1
                        except Exception as e:
                            logger.error(f"Error marking attendance for student_id={student_id}: {str(e)}")
                
                # Mark absent students
                all_enrolled_ids = [s["id"] for s in all_enrolled_students]
                absent_student_ids = [sid for sid in all_enrolled_ids if sid not in marked_ids]
                
                if absent_student_ids:
                    for student_id in absent_student_ids:
                        try:
                            success = mark_attendance(student_id, subject_id_val, selected_date, selected_period, status="absent")
                            if success:
                                absent_count += 1
                        except Exception as e:
                            logger.error(f"Error marking absent attendance for student_id={student_id}: {str(e)}")
                
                if success_count > 0 or absent_count > 0:
                    message = f"✅ Attendance saved for {success_count} present students"
                    if absent_count > 0:
                        message += f" and {absent_count} absent students"
                    message += f" on {selected_date}!"
                    st.success(message)
                    
                    st.session_state.last_attendance = {
                        'subject': selected_subject,
                        'date': selected_date,
                        'period': selected_period,
                        'count': success_count
                    }
                    
                    # Clear form submission state
                    st.session_state.attendance_form_submitted = False
                    del st.session_state.attendance_data
                    st.session_state.clear_attendance_form = True
                    st.rerun()
        except Exception as e:
            logger.error(f"Error processing attendance form: {str(e)}\n{traceback.format_exc()}")
            st.error(f"❌ Error marking attendance: {str(e)}")
            st.session_state.attendance_form_submitted = False
    
    # Process attendance button - just analyze, don't save yet
    if deepface_available and st.button("Analyze Image") and len(image_files) > 0 and subject_id is not None:
        # If processing all images is enabled and there are multiple images
        if process_all and len(image_files) > 1:
            st.subheader("Processing Multiple Images")
            
            # Create a container for all results
            all_results_container = st.container()
            
            # Initialize combined results
            all_detected_faces = 0
            all_recognized_students = set()  # Use a set to avoid duplicates
            all_confidence_scores = []
            total_processing_time = 0
            
            # Process each image
            for idx, img_file in enumerate(image_files):
                with st.spinner(f"Processing image {idx+1} of {len(image_files)}..."):
                    try:
                        # Record start time for performance metrics
                        start_time = time.time()
                        
                        # Prepare parameters for DeepFace verification
                        temp_image_path = None
                        
                        if is_uploaded_file(img_file):
                            # For uploaded files, save to a temporary file
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            temp_image_path = f"temp_image_{idx}_{timestamp}.jpg"
                            with open(temp_image_path, "wb") as f:
                                f.write(img_file.getvalue())
                            classroom_image = temp_image_path
                        else:
                            # For paths from ESP32-CAM
                            classroom_image = img_file
                        
                        # Detect all faces first to get count
                        detected_faces, face_locations = detect_faces_with_details(classroom_image, detector_backend=detector_backend)
                        
                        # Use the selected model with adjusted threshold for better recognition
                        present_students, confidence_scores = verify_faces(
                            classroom_image_path=classroom_image, 
                            students=get_all_students(),
                            threshold=threshold,
                            model_name=model_name,
                            return_confidence=True,
                            detector_backend=detector_backend
                        )
                        
                        # Calculate processing time
                        end_time = time.time()
                        processing_time = end_time - start_time
                        
                        # Update combined results
                        all_detected_faces += len(detected_faces)
                        all_recognized_students.update([student["id"] for student in present_students])
                        all_confidence_scores.extend(confidence_scores)
                        total_processing_time += processing_time
                        
                        # Display individual image results
                        st.write(f"### Image {idx+1} Results")
                        st.write(f"Detected faces: {len(detected_faces)}")
                        st.write(f"Recognized students: {len(present_students)}")
                        st.write(f"Processing time: {processing_time:.2f} seconds")
                        
                        # Clean up temporary file if created
                        if temp_image_path and os.path.exists(temp_image_path):
                            os.remove(temp_image_path)
                            
                    except Exception as e:
                        logger.error(f"Error processing image {idx+1}: {str(e)}\n{traceback.format_exc()}")
                        st.error(f"Error processing image {idx+1}: {str(e)}")
            
            # Display combined results
            with all_results_container:
                st.subheader("Combined Results")
                
                # Display metrics
                cols = st.columns(4)
                with cols[0]:
                    st.metric("Total Processing Time", f"{total_processing_time:.2f} sec")
                with cols[1]:
                    st.metric("Total Faces Detected", f"{all_detected_faces}")
                with cols[2]:
                    st.metric("Total Students Recognized", f"{len(all_recognized_students)}")
                with cols[3]:
                    recognition_rate = (len(all_recognized_students) / all_detected_faces * 100) if all_detected_faces > 0 else 0
                    st.metric("Overall Recognition Rate", f"{recognition_rate:.1f}%")
                
                # Display recognized students
                st.markdown("### All Recognized Students")
                
                # Get full details of all recognized students
                recognized_student_details = []
                for student_id in all_recognized_students:
                    student_details = get_student_details(student_id)
                    if student_details:
                        recognized_student_details.append(student_details)
                
                # Display in a grid
                if recognized_student_details:
                    grid_cols = st.columns(4)
                    for i, student in enumerate(recognized_student_details):
                        with grid_cols[i % 4]:
                            try:
                                img = Image.open(student["image_path"])
                                st.image(img, caption=f"{student['roll_no']}\n{student['name']}", width=150)
                            except Exception as e:
                                st.error(f"Error loading image: {str(e)}")
                    
                    # Automatically mark attendance for batch processing
                    # Get all enrolled students and recognized student IDs
                    all_enrolled_students = get_students_by_subject(subject_id)
                    recognized_student_ids = [student["id"] for student in recognized_student_details] if recognized_student_details else []
                    selected_date = attendance_date.strftime("%Y-%m-%d")
                    
                    # Automatically mark attendance
                    try:
                        logger.info(f"Auto-marking batch attendance: {len(recognized_student_ids)} recognized students. Subject: {subject_id}, Date: {selected_date}, Period: {selected_period}")
                        
                        if subject_id is None:
                            st.error("❌ Error: Subject ID is not available. Please select a subject and try again.")
                            logger.error("Subject ID is None when trying to mark attendance")
                        else:
                            success_count = 0
                            absent_count = 0
                            
                            # Mark present students (recognized)
                            if recognized_student_ids:
                                for student_id in recognized_student_ids:
                                    try:
                                        success = mark_attendance(student_id, subject_id, selected_date, selected_period, status="present")
                                        if success:
                                            success_count += 1
                                        else:
                                            logger.warning(f"Failed to mark attendance for student_id={student_id}")
                                    except Exception as e:
                                        logger.error(f"Error marking attendance for student_id={student_id}: {str(e)}")
                                        st.warning(f"Failed to mark attendance for student {student_id}: {str(e)}")
                            
                            # Mark absent students (those enrolled but not recognized)
                            all_enrolled_ids = [s["id"] for s in all_enrolled_students]
                            absent_student_ids = [sid for sid in all_enrolled_ids if sid not in recognized_student_ids]
                            
                            if absent_student_ids:
                                for student_id in absent_student_ids:
                                    try:
                                        success = mark_attendance(student_id, subject_id, selected_date, selected_period, status="absent")
                                        if success:
                                            absent_count += 1
                                    except Exception as e:
                                        logger.error(f"Error marking absent attendance for student_id={student_id}: {str(e)}")
                            
                            if success_count > 0 or absent_count > 0:
                                message = f"✅ Attendance automatically saved for {success_count} present students"
                                if absent_count > 0:
                                    message += f" and {absent_count} absent students"
                                message += f" on {selected_date}!"
                                st.success(message)
                                logger.info(f"Successfully saved attendance for {success_count} present and {absent_count} absent students")
                                
                                # Store attendance data in session state
                                st.session_state.last_attendance = {
                                    'subject': selected_subject,
                                    'date': selected_date,
                                    'period': selected_period,
                                    'count': success_count
                                }
                            else:
                                st.warning("⚠️ No attendance was marked. Please check the logs.")
                                logger.warning("No students were successfully marked for attendance")
                    except Exception as e:
                        logger.error(f"Error in automatic batch attendance marking: {str(e)}\n{traceback.format_exc()}")
                        st.error(f"❌ Error marking attendance: {str(e)}")
                        st.info("Please check the logs for more details.")
                    
                    # Visual representation of recognized students
                    st.markdown("### Student Photos")
                    cols = st.columns(4)
                    col_idx = 0
                    
                    for student in present_students:
                        # Display student face image
                        with cols[col_idx]:
                            try:
                                img = Image.open(student["image_path"])
                                st.image(img, caption=f"{student['roll_no']}\n{student['name']}", width=150)
                                
                                # Add confidence score if available
                                idx = present_students.index(student)
                                if idx < len(confidence_scores):
                                    st.caption(f"Confidence: {confidence_scores[idx]:.2f}")
                            except Exception as e:
                                st.error(f"Error loading image: {str(e)}")
                            
                            # Move to next column
                            col_idx = (col_idx + 1) % 4
                    
                    # Clean up temporary file if created
                    if temp_image_path and os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                    
                else:
                    st.warning("No students were recognized in any of the images.")
        else:
            # Process single image (existing code)
            with st.spinner("Processing image using facial recognition..."):
                try:
                    # Record start time for performance metrics
                    start_time = time.time()
                    
                    # Get all students enrolled in the selected subject
                    all_students = get_all_students()
                    
                    # Check if we have students in database
                    if not all_students:
                        st.error("❌ No students found in database.")
                        st.info("""
                        **To fix this:**
                        1. Go to **👤 Student Registration** page to add students
                        2. Make sure students are enrolled in the selected subject
                        3. Check database connection in logs
                        
                        **Quick Check:**
                        - Database file: `db/attendance.db`
                        - Check if file exists and has proper permissions
                        """)
                    else:
                        # Prepare parameters for DeepFace verification
                        # Handle both uploaded file objects and file paths
                        temp_image_path = None
                        
                        if is_uploaded_file(image_file):
                            # For uploaded files, save to a temporary file
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            temp_image_path = f"temp_image_{timestamp}.jpg"
                            with open(temp_image_path, "wb") as f:
                                f.write(image_file.getvalue())
                            classroom_image = temp_image_path
                        else:
                            # For paths from ESP32-CAM
                            classroom_image = image_file
                        
                        # Detect all faces first to get count
                        detected_faces, face_locations = detect_faces_with_details(classroom_image)
                        
                        # Use the selected model with adjusted threshold for better recognition
                        present_students, confidence_scores = verify_faces(
                            classroom_image_path=classroom_image, 
                            students=all_students,
                            threshold=threshold,
                            model_name=model_name,
                            return_confidence=True
                        )
                        
                        # Calculate processing time
                        end_time = time.time()
                        processing_time = end_time - start_time
                        
                        # Save statistics to session state
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                        recognition_rate = (len(present_students) / len(detected_faces) * 100) if detected_faces else 0
                        
                        stats = {
                            'datetime': current_time,
                            'subject': selected_subject,
                            'period': selected_period,
                            'processing_time': processing_time,
                            'detected_faces': len(detected_faces),
                            'recognized_students': len(present_students),
                            'recognition_rate': recognition_rate,
                            'avg_confidence': avg_confidence
                        }
                        
                        save_session_stats(stats)
                        
                        # Display statistics
                        display_recognition_stats(
                            processing_time=processing_time,
                            detected_faces=len(detected_faces),
                            recognized_students=present_students,
                            confidence_scores=confidence_scores,
                            model_name=model_name
                        )
                        
                        # Display face detection visualization
                        visualize_detected_faces(classroom_image, face_locations, present_students)
                        
                        # Display attendance summary
                        st.subheader("Attendance Summary")
                        
                        # Show comparison of detected vs recognized faces
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info(f"**Detected Faces:** {len(detected_faces)}")
                            
                        with col2:
                            st.success(f"**Recognized Students:** {len(present_students)}")
                        
                        if len(detected_faces) > len(present_students):
                            st.warning(f"⚠️ {len(detected_faces) - len(present_students)} faces detected but not recognized. These may be students not registered in the system or false detections.")
                        
                        # Automatically mark attendance for recognized students
                        selected_date = attendance_date.strftime("%Y-%m-%d")
                        
                        # Get all students enrolled in this subject
                        all_enrolled_students = get_students_by_subject(subject_id)
                        present_student_ids = [student["id"] for student in present_students] if present_students else []
                        
                        # Automatically mark attendance
                        try:
                            logger.info(f"Auto-marking attendance: {len(present_student_ids)} recognized students. Subject: {subject_id}, Date: {selected_date}, Period: {selected_period}")
                            
                            if subject_id is None:
                                st.error("❌ Error: Subject ID is not available. Please select a subject and try again.")
                                logger.error("Subject ID is None when trying to mark attendance")
                            else:
                                success_count = 0
                                absent_count = 0
                                
                                # Mark present students (recognized)
                                if present_student_ids:
                                    for student_id in present_student_ids:
                                        try:
                                            success = mark_attendance(student_id, subject_id, selected_date, selected_period, status="present")
                                            if success:
                                                success_count += 1
                                            else:
                                                logger.warning(f"Failed to mark attendance for student_id={student_id}")
                                        except Exception as e:
                                            logger.error(f"Error marking attendance for student_id={student_id}: {str(e)}")
                                            st.warning(f"Failed to mark attendance for student {student_id}: {str(e)}")
                                
                                # Mark absent students (those enrolled but not recognized)
                                all_enrolled_ids = [s["id"] for s in all_enrolled_students]
                                absent_student_ids = [sid for sid in all_enrolled_ids if sid not in present_student_ids]
                                
                                if absent_student_ids:
                                    for student_id in absent_student_ids:
                                        try:
                                            success = mark_attendance(student_id, subject_id, selected_date, selected_period, status="absent")
                                            if success:
                                                absent_count += 1
                                        except Exception as e:
                                            logger.error(f"Error marking absent attendance for student_id={student_id}: {str(e)}")
                                
                                if success_count > 0 or absent_count > 0:
                                    message = f"✅ Attendance automatically saved for {success_count} present students"
                                    if absent_count > 0:
                                        message += f" and {absent_count} absent students"
                                    message += f" on {selected_date}!"
                                    st.success(message)
                                    logger.info(f"Successfully saved attendance for {success_count} present and {absent_count} absent students")
                                    
                                    # Store attendance data in session state
                                    st.session_state.last_attendance = {
                                        'subject': selected_subject,
                                        'date': selected_date,
                                        'period': selected_period,
                                        'count': success_count
                                    }
                                else:
                                    st.warning("⚠️ No attendance was marked. Please check the logs.")
                                    logger.warning("No students were successfully marked for attendance")
                        except Exception as e:
                            logger.error(f"Error in automatic attendance marking: {str(e)}\n{traceback.format_exc()}")
                            st.error(f"❌ Error marking attendance: {str(e)}")
                            st.info("Please check the logs for more details.")
                        
                        # Display recognized students in a table for reference
                        if present_students:
                            st.markdown("### Recognized Students (Reference)")
                            student_data = []
                            for student in present_students:
                                student_data.append({
                                    "Roll No": student["roll_no"],
                                    "Name": student["name"],
                                    "Status": "✅ Present"
                                })
                            
                            student_df = pd.DataFrame(student_data)
                            st.dataframe(student_df, use_container_width=True)
                            
                            # Visual representation of recognized students
                            st.markdown("### Student Photos")
                            cols = st.columns(4)
                            col_idx = 0
                            
                            for student in present_students:
                                # Display student face image
                                with cols[col_idx]:
                                    try:
                                        img = Image.open(student["image_path"])
                                        st.image(img, caption=f"{student['roll_no']}\n{student['name']}", width=150)
                                        
                                        # Add confidence score if available
                                        idx = present_students.index(student)
                                        if idx < len(confidence_scores):
                                            st.caption(f"Confidence: {confidence_scores[idx]:.2f}")
                                    except Exception as e:
                                        st.error(f"Error loading image: {str(e)}")
                                    
                                    # Move to next column
                                    col_idx = (col_idx + 1) % 4
                            
                            # Clean up temporary file if created
                            if temp_image_path and os.path.exists(temp_image_path):
                                os.remove(temp_image_path)
                        
                        else:
                            st.warning("No students were recognized in any of the images.")
                except Exception as e:
                    logger.error(f"Error processing attendance: {str(e)}\n{traceback.format_exc()}")
                    st.error(f"Error processing attendance: {str(e)}")
    elif not deepface_available and st.button("Analyze Image"):
        st.error("DeepFace module is not available. Please check installation and dependencies.")

elif page == "Attendance Reports":
    # Check permission
    if not can_access_feature(user, 'view_class_reports'):
        st.error("❌ Access Denied: You do not have permission to view attendance reports.")
    else:
        st.title("📊 Attendance Reports")
        
        try:
            pass
        except Exception as e:
            logger.error(f"Error loading attendance report page: {str(e)}")
            st.error(f"Error: {str(e)}")

        # Get subjects from database
        subjects = get_subjects()
        subject_options = [subject[1] for subject in subjects]  # Use code instead of full name
        
        if subject_options:
            selected_subject = st.selectbox("Select Subject", subject_options)
            subject_id = next((subject[0] for subject in subjects if subject[1] == selected_subject), None)
            
            # Date selection
            report_date = st.date_input("Select Date", value=datetime.date.today())
            
            # Get attendance report
            if subject_id:
                attendance_data = get_attendance_report(subject_id, report_date.strftime("%Y-%m-%d"))
                
                if attendance_data:
                    st.subheader(f"Attendance for {selected_subject} on {report_date}")
                    
                    try:
                        # Create DataFrame for display with proper status icons
                        # attendance_data format: (id, roll_no, name, email, status, period, not_marked)
                        status_display = []
                        for data in attendance_data:
                            status = data[4] if len(data) > 4 else 'not_marked'
                            if status == "present":
                                status_display.append("✅ Present")
                            elif status == "absent":
                                status_display.append("❌ Absent")
                            else:  # not_marked
                                status_display.append("⏸️ Not Marked")
                        
                        df = pd.DataFrame(
                            [(data[1], data[2], data[3], status_display[i]) for i, data in enumerate(attendance_data)],
                            columns=["Roll No", "Name", "Email", "Status"]
                        )
                        st.dataframe(df)
                        
                        # Calculate and display statistics
                        present_count = sum(1 for data in attendance_data if len(data) > 4 and data[4] == "present")
                        absent_count = sum(1 for data in attendance_data if len(data) > 4 and data[4] == "absent")
                        not_marked_count = sum(1 for data in attendance_data if len(data) > 4 and data[4] == "not_marked")
                        total_count = len(attendance_data)
                        
                        # Display metrics
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total Students", str(total_count))
                        with col2:
                            st.metric("✅ Present", str(present_count))
                        with col3:
                            st.metric("❌ Absent", str(absent_count))
                        with col4:
                            st.metric("⏸️ Not Marked", str(not_marked_count))
                        with col5:
                            attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0
                            st.metric("Attendance %", f"{attendance_percentage:.1f}%")
                        
                        # Show pie chart
                        chart_data = pd.DataFrame({
                            'Status': ['Present', 'Absent', 'Not Marked'],
                            'Count': [present_count, absent_count, not_marked_count]
                        })
                        if present_count > 0 or absent_count > 0 or not_marked_count > 0:
                            st.subheader("Attendance Visualization")
                            st.bar_chart(chart_data.set_index('Status'))
                        
                        # Export to Excel
                        excel_path = os.path.join("excel_exports", f"{selected_subject}_{department}_{year}{division}.xlsx")
                        
                        # Create pivot table for Excel export
                        pivot_data = []
                        for data in attendance_data:
                            status = data[4] if len(data) > 4 else 'not_marked'
                            if status == "present":
                                status_icon = "✅"
                            elif status == "absent":
                                status_icon = "❌"
                            else:  # not_marked
                                status_icon = "⏸️"
                            
                            pivot_data.append({
                                "Roll No": data[1],
                                "Name": data[2],
                                "Email": data[3],
                                report_date.strftime("%Y-%m-%d"): status_icon
                            })
                        
                        pivot_df = pd.DataFrame(pivot_data)
                        
                        # Track the final dataframe for Google Sheets export
                        final_df_for_export = pivot_df
                        
                        try:
                            # Check if file exists already
                            if os.path.exists(excel_path):
                                # Read existing Excel and merge with new data
                                try:
                                    # Use pandas with proper file closing
                                    existing_df = None
                                    try:
                                        existing_df = pd.read_excel(excel_path)
                                        
                                        # Merge the dataframes
                                        merged_df = pd.merge(existing_df, pivot_df, on=["Roll No", "Name", "Email"], how="outer")
                                        final_df_for_export = merged_df
                                        # Save with context manager to ensure file is closed
                                        with pd.ExcelWriter(excel_path, mode='w') as writer:
                                            merged_df.to_excel(writer, index=False)
                                    except Exception as excel_read_error:
                                        logger.error(f"Error reading existing Excel: {str(excel_read_error)}")
                                        # If existing file has issues, just write the new one
                                        final_df_for_export = pivot_df
                                        with pd.ExcelWriter(excel_path, mode='w') as writer:
                                            pivot_df.to_excel(writer, index=False)
                                except Exception as excel_write_error:
                                    logger.error(f"Error writing Excel file: {str(excel_write_error)}")
                                    # Try one more time with a different approach
                                    try:
                                        # Use a new filename if the original is locked
                                        alt_excel_path = excel_path.replace(".xlsx", f"_{int(time.time())}.xlsx")
                                        final_df_for_export = pivot_df
                                        pivot_df.to_excel(alt_excel_path, index=False)
                                        excel_path = alt_excel_path
                                    except Exception as e:
                                        logger.error(f"All Excel write attempts failed: {str(e)}")
                                        raise
                            else:
                                # Create new Excel file with context manager
                                final_df_for_export = pivot_df
                                with pd.ExcelWriter(excel_path, mode='w') as writer:
                                    pivot_df.to_excel(writer, index=False)
                            
                            # Only try to open the file for download if it exists
                            if os.path.exists(excel_path):
                                with open(excel_path, "rb") as file:
                                    st.download_button(
                                        label="Download Excel Report",
                                        data=file,
                                        file_name=f"{selected_subject}_{report_date}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                            
                            # Export to Google Sheets in parallel
                            if sheets_available:
                                try:
                                    # Remove Email column if present for Google Sheets (optional)
                                    if "Email" in final_df_for_export.columns:
                                        df_to_export_sheets = final_df_for_export.drop(columns=["Email"])
                                    else:
                                        df_to_export_sheets = final_df_for_export
                                    
                                    if update_attendance_sheet(df_to_export_sheets, selected_subject):
                                        sheets_info = get_spreadsheet_info()
                                        if sheets_info and sheets_info.get('url'):
                                            st.success(f"✅ Attendance data exported to Google Sheets")
                                            st.info(f"📊 [Open Google Sheet]({sheets_info['url']})")
                                        else:
                                            st.success(f"✅ Attendance data also exported to Google Sheets")
                                    else:
                                        logger.warning("Google Sheets export failed, but Excel export succeeded")
                                except Exception as sheets_error:
                                    logger.error(f"Error exporting to Google Sheets: {str(sheets_error)}")
                                    # Don't show error to user if Excel succeeded - Sheets is optional
                        except Exception as excel_error:
                            logger.error(f"Error exporting to Excel: {str(excel_error)}")
                            st.error(f"Error exporting to Excel: {str(excel_error)}")
                        
                        # Option to notify absent students (both marked absent and not marked)
                        # Filter for students who are either marked absent or not marked at all
                        absent_students = df[df["Status"].str.contains("❌|⏸️", na=False)]
                        if not absent_students.empty and st.button("Send Email Notifications to Absent/Not Marked Students"):
                            try:
                                from utils.email_utils import send_bulk_attendance_emails
                                from config import EMAIL_ENABLED
                                
                                if not EMAIL_ENABLED:
                                    st.warning("⚠️ Email notifications are disabled. Please enable EMAIL_ENABLED in configuration.")
                                else:
                                    # Prepare attendance records for email sending
                                    attendance_records = []
                                    for _, student in absent_students.iterrows():
                                        if student["Email"] and pd.notna(student["Email"]) and str(student["Email"]).strip():
                                            # Determine status from the Status column
                                            status_text = student["Status"]
                                            if "⏸️" in status_text or "Not Marked" in status_text:
                                                email_status = 'not_marked'
                                            else:
                                                email_status = 'absent'
                                            
                                            attendance_records.append({
                                                'email': str(student["Email"]).strip(),
                                                'name': student["Name"],
                                                'roll_no': student["Roll No"],
                                                'status': email_status
                                            })
                                    
                                    if attendance_records:
                                        # Show email configuration status
                                        from config import EMAIL_ENABLED, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM
                                        
                                        config_status = []
                                        config_status.append(f"**Email Configuration:**")
                                        config_status.append(f"- Enabled: {EMAIL_ENABLED}")
                                        config_status.append(f"- SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
                                        config_status.append(f"- From Address: {EMAIL_FROM}")
                                        config_status.append(f"- Username: {SMTP_USERNAME if SMTP_USERNAME else 'NOT SET'}")
                                        config_status.append(f"- Password: {'SET' if SMTP_PASSWORD else 'NOT SET'}")
                                        
                                        with st.expander("📧 Email Configuration Status", expanded=False):
                                            st.markdown("\n".join(config_status))
                                        
                                        with st.spinner(f"Sending email notifications to {len(attendance_records)} absent students..."):
                                            # Get period from attendance data
                                            # Period is now included in attendance_data (index 5)
                                            # The database query now returns the most common period for absent students
                                            period = "N/A"
                                            if attendance_data and len(attendance_data) > 0:
                                                try:
                                                    # Get period from any record (present students have actual periods)
                                                    # The database query fills in the most common period for absent students
                                                    for record in attendance_data:
                                                        if len(record) > 5 and record[5] and record[5] != "N/A" and record[5] != "None":
                                                            period = record[5]
                                                            logger.info(f"Using period from attendance data: {period}")
                                                            break
                                                    
                                                    # If still N/A, try to get from present students
                                                    if period == "N/A":
                                                        for record in attendance_data:
                                                            if len(record) > 4 and record[4] == "present" and len(record) > 5:
                                                                if record[5] and record[5] != "N/A" and record[5] != "None":
                                                                    period = record[5]
                                                                    logger.info(f"Using period from present student record: {period}")
                                                                    break
                                                except Exception as e:
                                                    logger.warning(f"Error extracting period: {str(e)}")
                                                    period = "N/A"
                                            
                                            if period == "N/A":
                                                logger.warning(f"Could not determine period for date {report_date}. Using 'N/A'")
                                            
                                            logger.info(f"Starting bulk email send for {len(attendance_records)} students")
                                            results = send_bulk_attendance_emails(
                                                attendance_records=attendance_records,
                                                subject_name=selected_subject,
                                                date=report_date.strftime("%Y-%m-%d"),
                                                period=period
                                            )
                                            
                                            # Display detailed results
                                            if results['sent'] > 0:
                                                st.success(f"✅ Successfully sent {results['sent']} email notification(s) to absent students")
                                            
                                            if results['failed'] > 0:
                                                st.error(f"❌ Failed to send {results['failed']} email(s).")
                                                
                                                # Show details if available
                                                if 'details' in results:
                                                    failed_details = [d for d in results['details'] if d['status'] == 'failed']
                                                    if failed_details:
                                                        with st.expander("❌ Failed Email Details", expanded=True):
                                                            for detail in failed_details:
                                                                st.write(f"- {detail['name']} ({detail['email']})")
                                                
                                                st.warning("⚠️ Check the application logs (app.log) for detailed error messages.")
                                                st.info("💡 **Troubleshooting:** Check your SMTP credentials, server settings, and network connectivity.")
                                            
                                            if results['sent'] == 0 and results['failed'] == 0:
                                                st.warning("⚠️ No emails were sent. Please check email configuration.")
                                            
                                            # Show log file location
                                            st.info(f"📋 **View detailed logs:** Check `app.log` file in the project directory for complete email sending logs.")
                                    else:
                                        st.warning("No valid email addresses found for absent students.")
                            except ImportError as e:
                                st.error(f"Email utilities not available: {str(e)}")
                                logger.error(f"Error importing email utilities: {str(e)}")
                            except Exception as e:
                                st.error(f"Error sending email notifications: {str(e)}")
                                logger.error(f"Error sending email notifications: {str(e)}\n{traceback.format_exc()}")
                    except Exception as df_error:
                        logger.error(f"Error processing attendance data: {str(df_error)}")
                        st.error(f"Error processing attendance data: {str(df_error)}")
                else:
                    st.info(f"No attendance records found for {selected_subject} on {report_date}")
        else:
            st.warning("No subjects found in database. Please check database configuration.")

elif page == "Recognition Stats":
    # Check permission
    if not can_access_feature(user, 'view_analytics'):
        st.error("❌ Access Denied: You do not have permission to view recognition statistics.")
    else:
        st.title("👁️ Facial Recognition Analytics")
        try:
            pass
        except Exception as e:
            logger.error(f"Error loading recognition stats page: {str(e)}")
            st.error(f"Error: {str(e)}")
        st.write("""
        This page provides detailed analytics about the facial recognition system performance.
        View statistics on recognition accuracy, processing times, and system performance.
        """)
        
        # Get latest stats if available
        if 'recognition_stats' in st.session_state:
            stats = st.session_state.recognition_stats
            
            st.subheader("Overall System Performance")
            
            # Display metrics in a nice layout
            col1, col2, col3, col4 = st.columns(4)
            
            st.subheader("Overall System Performance")
            
            # Display metrics in a nice layout
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Avg. Processing Time", f"{stats.get('avg_processing_time', 0):.2f} sec")
            with col2:
                st.metric("Recognition Rate", f"{stats.get('recognition_rate', 0):.1f}%")
            with col3:
                st.metric("Avg. Confidence", f"{stats.get('avg_confidence', 0):.2f}")
            with col4:
                st.metric("Total Sessions", str(stats.get('total_sessions', 0)))
            
            # Display historical data if available
            if 'history' in stats and len(stats['history']) > 0:
                st.subheader("Historical Performance")
                
                # Create DataFrame from history
                history_df = pd.DataFrame(stats['history'])
                
                # Display line charts
                if 'recognition_rate' in history_df.columns:
                    st.line_chart(history_df[['recognition_rate']])
                if 'processing_time' in history_df.columns:
                    st.line_chart(history_df[['processing_time']])
            
            # Display most recent recognition details
            if 'last_session' in stats:
                last = stats['last_session']
                st.subheader("Last Recognition Session")
                
                st.write(f"Date/Time: {last.get('datetime', 'Unknown')}")
                st.write(f"Subject: {last.get('subject', 'Unknown')}")
                st.write(f"Period: {last.get('period', 'Unknown')}")
                
                # Display recognized vs. not recognized
                recognized = last.get('recognized_count', 0)
                not_recognized = last.get('total_faces', 0) - recognized
                
                chart_data = pd.DataFrame({
                    'Status': ['Recognized', 'Not Recognized'],
                    'Count': [recognized, not_recognized]
                })
                if recognized > 0 or not_recognized > 0:
                    st.bar_chart(chart_data.set_index('Status'))
            
            # Add detailed accuracy metrics section
            st.subheader("Detailed Accuracy Metrics")
            
            tabs = st.tabs(["Confusion Matrix", "Precision & Recall", "Accuracy Over Time"])
            
            with tabs[0]:
                # Confusion Matrix visualization
                st.write("Confusion Matrix")
                if 'confusion_matrix' in stats:
                    cm = stats['confusion_matrix']
                    
                    try:
                        # Create a basic confusion matrix visualization
                        cm_data = np.array([[cm.get('TP', 0), cm.get('FP', 0)], 
                                          [cm.get('FN', 0), cm.get('TN', 0)]])
                        
                        fig, ax = plt.subplots(figsize=(6, 5))
                        sns.heatmap(cm_data, annot=True, fmt='d', cmap='Blues',
                                  xticklabels=['Present', 'Absent'],
                                  yticklabels=['Present', 'Absent'])
                        plt.ylabel('Actual')
                        plt.xlabel('Predicted')
                        st.pyplot(fig)
                    except Exception as e:
                        logger.error(f"Error creating confusion matrix visualization: {str(e)}")
                        st.error("Could not create confusion matrix visualization. Make sure matplotlib and seaborn are installed.")
                        
                        # Fallback to text display
                        st.write("Confusion Matrix Data:")
                        st.write(f"True Positives: {cm.get('TP', 0)}")
                        st.write(f"False Positives: {cm.get('FP', 0)}")
                        st.write(f"False Negatives: {cm.get('FN', 0)}")
                        st.write(f"True Negatives: {cm.get('TN', 0)}")
                else:
                    # Create placeholder matrix with sample data
                    tp = stats.get('total_students_recognized', 0)
                    fn = stats.get('total_faces_detected', 0) - tp
                    
                    cm_data = pd.DataFrame({
                        '': ['Actual Present', 'Actual Absent'],
                        'Predicted Present': [tp, 0],  # We don't track false positives yet
                        'Predicted Absent': [fn, 0]    # We don't track true negatives yet
                    })
                    
                    st.write("Detected Faces vs. Recognized Students:")
                    st.dataframe(cm_data.set_index(''))
                    st.info("Note: Complete confusion matrix tracking requires manual verification of results.")
            
            with tabs[1]:
                # Calculate precision and recall if we have enough data
                if stats.get('total_students_recognized', 0) > 0:
                    # Simplified calculation based on available data
                    precision = 1.0  # Assuming all recognitions are correct
                    recall = (stats.get('total_students_recognized', 0) / 
                             stats.get('total_faces_detected', 0) if stats.get('total_faces_detected', 0) > 0 else 0)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Precision", f"{precision:.2f}")
                        st.caption("Correctly identified / Total identified")
                    with col2:
                        st.metric("Recall", f"{recall:.2f}")
                        st.caption("Correctly identified / Total actual faces")
                    
                    # F1 Score
                    if precision + recall > 0:
                        f1 = 2 * precision * recall / (precision + recall)
                        st.metric("F1 Score", f"{f1:.2f}")
                else:
                    st.info("Not enough data to calculate precision and recall metrics.")
            
            with tabs[2]:
                # Display accuracy over time if we have history
                if 'history' in stats and len(stats['history']) > 0:
                    history_df = pd.DataFrame(stats['history'])
                    if 'datetime' in history_df and 'recognition_rate' in history_df:
                        try:
                            history_df['datetime'] = pd.to_datetime(history_df['datetime'])
                            
                            # Plot accuracy over time
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.plot(history_df['datetime'], history_df['recognition_rate'], 'o-', linewidth=2)
                            ax.set_xlabel('Date/Time')
                            ax.set_ylabel('Recognition Rate (%)')
                            ax.set_title('Face Recognition Accuracy Over Time')
                            ax.grid(True)
                            
                            if len(history_df) > 5:
                                plt.xticks(rotation=45)
                            
                            st.pyplot(fig)
                        except Exception as e:
                            logger.error(f"Error creating accuracy over time plot: {str(e)}")
                            st.error("Could not create accuracy plot. Using simplified view instead.")
                            
                            # Fallback to simpler visualization
                            st.write("Recognition Rate Over Time:")
                            if 'datetime' in history_df.columns and 'recognition_rate' in history_df.columns:
                                simple_df = history_df[['datetime', 'recognition_rate']].copy()
                                simple_df['datetime'] = simple_df['datetime'].astype(str)
                                simple_df = simple_df.set_index('datetime')
                                st.line_chart(simple_df)
                    else:
                        st.info("Not enough historical data with timestamps to plot accuracy over time.")
                else:
                    st.info("No historical data available to show accuracy trends.")

            # Add instructions
            st.markdown("""
            ### How to generate recognition statistics:
            1. Go to the **Take Attendance** page
            2. Upload a classroom image or capture from camera
            3. Click **Analyze Image** to process the attendance
            4. The statistics will be automatically saved and displayed here
            """)
            
            # Add sample chart
            st.subheader("Sample Recognition Rate Chart (Demo)")
            sample_data = pd.DataFrame({
                'date': pd.date_range(start='2023-01-01', periods=5),
                'rate': [75, 82, 78, 88, 85]
            }).set_index('date')
            st.line_chart(sample_data)

elif page == "Class Reports":
    # Check permission
    if not can_access_feature(user, 'view_class_reports'):
        st.error("❌ Access Denied: You do not have permission to view class reports.")
    else:
        st.title("🏫 Class-wise Attendance Reports")
    st.markdown('<div class="dashboard-card"><p>View attendance statistics for the entire class across all subjects.</p></div>', unsafe_allow_html=True)
    
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            # Date range selection
            date_from = st.date_input("From Date", value=datetime.date.today() - datetime.timedelta(days=14))
        
        with col2:
            date_to = st.date_input("To Date", value=datetime.date.today())
            
        if date_from > date_to:
            st.error("Error: End date must fall after start date.")
        else:
            # Get summary statistics
            summary_data = get_class_attendance_summary(
                date_from.strftime("%Y-%m-%d"), 
                date_to.strftime("%Y-%m-%d")
            )
            
            if summary_data:
                # Convert to DataFrame
                df_summary = pd.DataFrame([
                    {
                        "Roll No": row["roll_no"],
                        "Name": row["name"],
                        "Division": row["division"],
                        "Present": row["present_count"],
                        "Total Classes": row["total_classes"],
                        "Attendance %": round(row["present_count"] / row["total_classes"] * 100, 1) if row["total_classes"] > 0 else 0
                    }
                    for row in summary_data
                ])
                
                # Summary metrics
                total_students = len(df_summary)
                avg_attendance = df_summary["Attendance %"].mean() if not df_summary.empty else 0
                below_75_count = len(df_summary[df_summary["Attendance %"] < 75]) if not df_summary.empty else 0
                
                # Display metrics
                st.markdown("### Overall Attendance")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Students", str(total_students))
                with col2:
                    st.metric("Avg. Attendance", f"{avg_attendance:.1f}%")
                with col3:
                    st.metric("Below 75%", str(below_75_count))
                with col4:
                    st.metric("Date Range", f"{(date_to - date_from).days + 1} days")
                
                # Attendance distribution
                st.markdown("### Attendance Distribution")
                
                # Create bins for attendance percentage
                bins = [0, 25, 50, 75, 90, 100]
                labels = ["0-25%", "26-50%", "51-75%", "76-90%", "91-100%"]
                
                # Add a new column with binned values
                df_summary["Attendance Range"] = pd.cut(df_summary["Attendance %"], bins=bins, labels=labels, right=True)
                
                # Count students in each bin
                attendance_dist = df_summary["Attendance Range"].value_counts().sort_index()
                
                # Create a color scale based on attendance
                colors = ["#f44336", "#ff9800", "#ffeb3b", "#8bc34a", "#4caf50"]
                
                # Create a bar chart with plotly
                fig = go.Figure(data=[
                    go.Bar(
                        x=attendance_dist.index,
                        y=attendance_dist.values,
                        text=attendance_dist.values,
                        textposition='auto',
                        marker_color=colors[:len(attendance_dist)]
                    )
                ])
                
                fig.update_layout(
                    title="Number of Students by Attendance Range",
                    xaxis_title="Attendance Range",
                    yaxis_title="Number of Students",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display the full dataset with conditional formatting
                st.markdown("### Student-wise Attendance")
                
                # Add color formatting based on attendance percentage
                def color_attendance(val):
                    if val < 50:
                        return 'color: #f44336; font-weight: bold'  # Red
                    elif val < 75:
                        return 'color: #ff9800; font-weight: bold'  # Orange
                    else:
                        return 'color: #4caf50; font-weight: bold'  # Green
                
                # Apply the formatting to the attendance percentage column
                styled_df = df_summary.style.applymap(
                    color_attendance, 
                    subset=pd.IndexSlice[:, ['Attendance %']]
                )
                
                st.dataframe(styled_df, use_container_width=True, height=400)
                
                # Add subject-wise attendance breakdown
                st.markdown("### Subject-wise Attendance")
                
                # Create tabs for each subject
                try:
                    subjects = get_subjects()
                    if subjects:
                        subject_tabs = st.tabs([subject[1] for subject in subjects])
                        
                        for i, subject in enumerate(subjects):
                            with subject_tabs[i]:
                                subject_id = subject[0]
                                subject_code = subject[1]  # This is the code (e.g., "FOC", "DSAJ")
                                # Note: get_subjects() returns (id, code, name), but we're using code as the display name
                                # So subject[1] is the code, which is what we need for SUBJECT_WEEKLY_CLASSES lookup
                                
                                # Get all dates in range
                                dates = []
                                current_date = date_from
                                while current_date <= date_to:
                                    dates.append(current_date.strftime("%Y-%m-%d"))
                                    current_date += datetime.timedelta(days=1)
                                
                                # Create a dictionary to store all attendance records
                                attendance_by_date = {}
                                
                                # For each date, get attendance report
                                for date_str in dates:
                                    attendance_data = get_attendance_report(subject_id, date_str)
                                    if attendance_data:
                                        attendance_by_date[date_str] = {
                                            data[1]: data[4] for data in attendance_data
                                        }
                                
                                if attendance_by_date:
                                    # Create a pivot table with students as rows and dates as columns
                                    rows = []
                                    for student in df_summary.to_dict('records'):
                                        roll_no = student["Roll No"]
                                        name = student["Name"]
                                        
                                        row = {"Roll No": roll_no, "Name": name}
                                        
                                        # Add attendance status for each date
                                        present_count = 0
                                        total_count = 0
                                        
                                        for date_str in dates:
                                            if date_str in attendance_by_date and roll_no in attendance_by_date[date_str]:
                                                status = attendance_by_date[date_str][roll_no]
                                                row[date_str] = "✅" if status == "present" else "❌"
                                                total_count += 1
                                                if status == "present":
                                                    present_count += 1
                                            else:
                                                row[date_str] = ""
                                        
                                        # Add summary statistics
                                        if total_count > 0:
                                            row["Present"] = present_count
                                            row["Total"] = total_count
                                            row["Attendance %"] = round(present_count / total_count * 100, 1)
                                        else:
                                            row["Present"] = 0
                                            row["Total"] = 0
                                            row["Attendance %"] = 0.0
                                            
                                        rows.append(row)
                                    
                                    # Convert to DataFrame
                                    subject_df = pd.DataFrame(rows)
                                    
                                    # Calculate expected classes based on weekly schedule
                                    try:
                                        from config import SUBJECT_WEEKLY_CLASSES
                                        from utils.db_utils import calculate_expected_classes
                                        
                                        # Use subject code to lookup weekly classes
                                        weekly_classes = SUBJECT_WEEKLY_CLASSES.get(subject_code, 0)
                                        date_from_str = date_from.strftime("%Y-%m-%d")
                                        date_to_str = date_to.strftime("%Y-%m-%d")
                                        expected_classes = calculate_expected_classes(subject_code, date_from_str, date_to_str)
                                    except Exception as e:
                                        logger.warning(f"Error calculating expected classes: {str(e)}")
                                        weekly_classes = 0
                                        expected_classes = len(dates)
                                    
                                    # Display summary statistics
                                    avg_attendance = subject_df["Attendance %"].mean() if len(subject_df) > 0 else 0
                                    below_75_count = len(subject_df[subject_df["Attendance %"] < 75]) if len(subject_df) > 0 else 0
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Average Attendance", f"{avg_attendance:.1f}%")
                                    with col2:
                                        st.metric("Students Below 75%", str(below_75_count))
                                    with col3:
                                        st.metric("Actual Classes", str(len(dates)))
                                    with col4:
                                        if weekly_classes > 0:
                                            st.metric("Expected Classes", f"{expected_classes} ({weekly_classes}/week)")
                                        else:
                                            st.metric("Expected Classes", "N/A")
                                    
                                    # Display attendance data
                                    summary_cols = ["Roll No", "Name", "Present", "Total", "Attendance %"]
                                    detail_cols = ["Roll No", "Name"] + dates + ["Attendance %"]
                                    
                                    # Create tabs for summary and detailed views
                                    view_tabs = st.tabs(["Summary", "Detailed"])
                                    
                                    with view_tabs[0]:
                                        # Display summary view
                                        styled_subject_df = subject_df[summary_cols].style.applymap(
                                            color_attendance, 
                                            subset=pd.IndexSlice[:, ['Attendance %']]
                                        )
                                        st.dataframe(styled_subject_df, use_container_width=True)
                                    
                                    with view_tabs[1]:
                                        # Display detailed view with dates
                                        st.dataframe(subject_df[detail_cols], use_container_width=True)
                                    
                                    # Export to Excel
                                    excel_path = os.path.join("excel_exports", f"{subject_name}_{department}_{year}{division}.xlsx")
                                    
                                    # Track the final dataframe for Google Sheets export
                                    final_df_for_sheets = subject_df
                                    
                                    # Auto-update Excel file
                                    try:
                                        # First, check if the file exists and try to read it
                                        if os.path.exists(excel_path):
                                            try:
                                                print(f"DEBUG: Reading existing Excel file: {excel_path}")
                                                existing_df = pd.read_excel(excel_path)
                                                
                                                # Get existing dates in the Excel file
                                                existing_dates = [col for col in existing_df.columns if col not in ["Roll No", "Name", "Present", "Total", "Attendance %"]]
                                                
                                                # Merge with new data
                                                for date_str in dates:
                                                    if date_str not in existing_dates:
                                                        # Add new date column
                                                        for _, row in subject_df.iterrows():
                                                            roll_no = row["Roll No"]
                                                            existing_df.loc[existing_df["Roll No"] == roll_no, date_str] = row.get(date_str, "")
                                                
                                                # Recalculate summary statistics
                                                for i, row in existing_df.iterrows():
                                                    present_count = sum(1 for col in existing_df.columns if col not in ["Roll No", "Name", "Present", "Total", "Attendance %"] and row[col] == "✅")
                                                    total_count = sum(1 for col in existing_df.columns if col not in ["Roll No", "Name", "Present", "Total", "Attendance %"] and row[col] in ["✅", "❌"])
                                                    
                                                    existing_df.at[i, "Present"] = present_count
                                                    existing_df.at[i, "Total"] = total_count
                                                    existing_df.at[i, "Attendance %"] = round(present_count / total_count * 100, 1) if total_count > 0 else 0.0
                                                
                                                # Save updated Excel file
                                                existing_df.to_excel(excel_path, index=False)
                                                final_df_for_sheets = existing_df
                                                st.success(f"Automatically updated {subject_name} Excel file with new attendance data.")
                                                print(f"DEBUG: Excel write successful")
                                            except Exception as e:
                                                # If reading fails, just write a new file
                                                logger.error(f"Error reading existing Excel file: {str(e)}")
                                                final_df_for_sheets = subject_df
                                                subject_df.to_excel(excel_path, index=False)
                                        else:
                                            # Create new Excel file
                                            final_df_for_sheets = subject_df
                                            subject_df.to_excel(excel_path, index=False)
                                            
                                        # Provide download button
                                        with open(excel_path, "rb") as file:
                                            st.download_button(
                                                label=f"Download {subject_name} Excel Report",
                                                data=file,
                                                file_name=f"{subject_name}_Attendance.xlsx",
                                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                key=f"download_{subject_name}"
                                            )
                                        
                                        # Export to Google Sheets in parallel
                                        if sheets_available:
                                            try:
                                                if update_attendance_sheet(final_df_for_sheets, subject_name):
                                                    sheets_info = get_spreadsheet_info()
                                                    if sheets_info and sheets_info.get('url'):
                                                        st.success(f"✅ {subject_name} attendance data exported to Google Sheets")
                                                        st.info(f"📊 [Open Google Sheet]({sheets_info['url']})")
                                                    else:
                                                        st.success(f"✅ {subject_name} attendance data also exported to Google Sheets")
                                                else:
                                                    logger.warning(f"Google Sheets export failed for {subject_name}, but Excel export succeeded")
                                            except Exception as sheets_error:
                                                logger.error(f"Error exporting {subject_name} to Google Sheets: {str(sheets_error)}")
                                                # Don't show error to user if Excel succeeded - Sheets is optional
                                    except Exception as excel_error:
                                        logger.error(f"Error with Excel operations: {str(excel_error)}")
                                        st.error(f"Error creating/updating Excel file: {str(excel_error)}")
                                else:
                                    st.info(f"No attendance records found for {subject_name} in the selected date range.")
                except Exception as e:
                    logger.error(f"Error displaying subject-wise attendance: {str(e)}")
                    st.error(f"Error displaying subject-wise attendance: {str(e)}")
                
                # Export overall class report to Excel
                excel_path = os.path.join("excel_exports", f"Class_Report_{department}_{year}{division}_{date_from}_to_{date_to}.xlsx")
                try:
                    # Using context manager to ensure the file is properly closed
                    with pd.ExcelWriter(excel_path, mode='w') as writer:
                        df_summary.to_excel(writer, index=False)
                    st.success(f"Class report saved to {excel_path}")
                    
                    # Export to Google Sheets in parallel
                    if sheets_available:
                        try:
                            worksheet_name = f"Class_Report_{date_from}_to_{date_to}"
                            if export_to_sheets(df_summary, worksheet_name):
                                sheets_info = get_spreadsheet_info()
                                if sheets_info and sheets_info.get('url'):
                                    st.success(f"✅ Class report exported to Google Sheets")
                                    st.info(f"📊 [Open Google Sheet]({sheets_info['url']})")
                                else:
                                    st.success(f"✅ Class report also exported to Google Sheets")
                            else:
                                logger.warning("Google Sheets export failed for class report, but Excel export succeeded")
                        except Exception as sheets_error:
                            logger.error(f"Error exporting class report to Google Sheets: {str(sheets_error)}")
                except Exception as e:
                    logger.error(f"Error exporting class report to Excel: {str(e)}")
                    st.error(f"Failed to export class report: {str(e)}")
            else:
                st.info(f"No attendance data found for the selected date range ({date_from} to {date_to}).")
    
    except Exception as e:
        logger.error(f"Error generating class report: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error: {str(e)}")

elif page == "Student Reports":
    st.title("👨‍🎓 Student-wise Attendance Reports")
    st.markdown('<div class="dashboard-card"><p>View detailed attendance for individual students.</p></div>', unsafe_allow_html=True)
    
    try:
        # Get all students
        all_students = get_all_students()
        
        if not all_students:
            st.error("❌ No students found in database.")
            st.info("""
            **To add students:**
            1. Navigate to **👤 Student Registration** page
            2. Register students with their photos
            3. Students will be automatically enrolled in subjects
            
            **Troubleshooting:**
            - Check database file exists: `db/attendance.db`
            - Verify database is initialized (check logs)
            - Ensure you have proper permissions
            """)
        else:
            # Convert to DataFrame for selection
            students_df = pd.DataFrame([
                {"id": student["id"], "roll_no": student["roll_no"], "name": student["name"]}
                for student in all_students
            ])
            
            # Create a search box for students
            search_term = st.text_input("Search student by roll number or name:")
            
            if search_term:
                filtered_students = students_df[
                    students_df["roll_no"].str.contains(search_term, case=False) | 
                    students_df["name"].str.contains(search_term, case=False)
                ]
            else:
                filtered_students = students_df
            
            # Display students in a selectbox
            student_options = [f"{row['roll_no']} - {row['name']}" for _, row in filtered_students.iterrows()]
            
            if student_options:
                selected_student_option = st.selectbox("Select Student:", student_options)
                selected_roll_no = selected_student_option.split(" - ")[0]
                
                try:
                    # Get student ID
                    student_id = students_df[students_df["roll_no"] == selected_roll_no]["id"].values[0]
                    
                    # Get student details
                    student_details = get_student_details(student_id)
                    
                    if student_details is None:
                        st.error("Student details not found in database. The student may have been deleted.")
                    else:
                        # Create tabs for different views
                        tab1, tab2 = st.tabs(["Summary", "Detailed Report"])
                        
                        with tab1:
                            # Display student information
                            col1, col2 = st.columns([1, 3])
                            
                            with col1:
                                try:
                                    # Display student image
                                    img = Image.open(student_details["image_path"])
                                    st.image(img, width=150)
                                except:
                                    st.info("No image available")
                            
                            with col2:
                                st.markdown(f"### {student_details['name']}")
                                st.markdown(f"**Roll No:** {student_details['roll_no']}")
                                st.markdown(f"**Email:** {student_details['email'] or 'N/A'}")
                                st.markdown(f"**Department:** {student_details['department']} | **Year:** {student_details['year']} | **Division:** {student_details['division']}")
                            
                            # Get attendance summary
                            attendance_summary = get_student_attendance_summary(student_id)
                            
                            if attendance_summary:
                                # Convert to DataFrame
                                df_summary = pd.DataFrame([
                                    {
                                        "Subject Code": row["subject_code"],
                                        "Subject Name": row["subject_name"],
                                        "Present": row["present_count"],
                                        "Total Classes": row["total_classes"],
                                        "Expected Classes": row.get("expected_classes", "N/A"),
                                        "Attendance %": round(row["present_count"] / row["total_classes"] * 100, 1) if row["total_classes"] > 0 else 0
                                    }
                                    for row in attendance_summary
                                ])
                                
                                # Calculate overall attendance percentage
                                overall_present = df_summary["Present"].sum()
                                overall_total = df_summary["Total Classes"].sum()
                                overall_percentage = round(overall_present / overall_total * 100, 1) if overall_total > 0 else 0
                                
                                # Show overall stats
                                st.markdown("### Overall Attendance")
                                
                                # Determine status color based on attendance
                                status_color = "#4caf50" if overall_percentage >= 75 else "#ff9800" if overall_percentage >= 50 else "#f44336"
                                
                                # Create attendance gauge chart
                                fig = go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=overall_percentage,
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Overall Attendance"},
                                    gauge={
                                        'axis': {'range': [0, 100]},
                                        'bar': {'color': status_color},
                                        'steps': [
                                            {'range': [0, 50], 'color': "#ffcdd2"},
                                            {'range': [50, 75], 'color': "#ffecb3"},
                                            {'range': [75, 100], 'color': "#c8e6c9"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': 75
                                        }
                                    }
                                ))
                                
                                fig.update_layout(height=250)
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Show subject-wise attendance
                                st.markdown("### Subject-wise Attendance")
                                
                                # Create bar chart for subject-wise attendance
                                fig = px.bar(
                                    df_summary,
                                    x="Subject Code",
                                    y="Attendance %",
                                    title="Subject-wise Attendance Percentage",
                                    color="Attendance %",
                                    color_continuous_scale=["red", "orange", "green"],
                                    range_color=[0, 100],
                                    text="Attendance %"
                                )
                                
                                fig.update_layout(height=400)
                                fig.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="Attendance Threshold (75%)")
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Display the detailed table
                                st.markdown("### Subject Details")
                                
                                # Add color formatting based on attendance percentage
                                def color_attendance(val):
                                    if val < 50:
                                        return 'color: #f44336; font-weight: bold'  # Red
                                    elif val < 75:
                                        return 'color: #ff9800; font-weight: bold'  # Orange
                                    else:
                                        return 'color: #4caf50; font-weight: bold'  # Green
                                
                                # Apply the formatting to the attendance percentage column
                                styled_df = df_summary.style.applymap(
                                    color_attendance, 
                                    subset=pd.IndexSlice[:, ['Attendance %']]
                                )
                                
                                st.dataframe(styled_df, use_container_width=True)
                            else:
                                st.info("No attendance data found for this student.")
                        
                        with tab2:
                            # Get detailed attendance report
                            attendance_report = get_student_attendance_report(student_id)
                            
                            if attendance_report:
                                # Convert to DataFrame
                                df_report = pd.DataFrame([
                                    {
                                        "Date": row["date"],
                                        "Subject": f"{row['subject_code']} - {row['subject_name']}",
                                        "Period": row["period"],
                                        "Status": "✅" if row["status"] == "present" else "❌"
                                    }
                                    for row in attendance_report
                                ])
                                
                                # Convert date column to datetime
                                df_report["Date"] = pd.to_datetime(df_report["Date"])
                                
                                # Add day of week column
                                df_report["Day"] = df_report["Date"].dt.day_name()
                                
                                # Group by date to create calendar view
                                cal_data = df_report.groupby("Date")["Status"].agg(
                                    lambda x: "✅" if all(s == "✅" for s in x) else 
                                              "❌" if all(s == "❌" for s in x) else "⚠️"
                                )
                                
                                st.markdown("### Attendance Calendar")
                                
                                # Create a monthly view
                                months = sorted(df_report["Date"].dt.to_period("M").unique())
                                
                                for month_period in months:
                                    month_start = month_period.start_time
                                    month_name = month_start.strftime("%B %Y")
                                    
                                    st.markdown(f"#### {month_name}")
                                    
                                    # Filter data for this month
                                    month_data = cal_data[cal_data.index.to_period("M") == month_period]
                                    
                                    # Create a calendar for this month
                                    _, num_days = calendar.monthrange(month_start.year, month_start.month)
                                    
                                    # Create a 7x6 calendar layout (7 days per week, up to 6 weeks)
                                    calendar_data = []
                                    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                                    
                                    # Create week rows
                                    first_day_weekday = month_start.replace(day=1).weekday()  # 0 is Monday
                                    day_count = 1
                                    
                                    for week in range(6):  # Max 6 weeks in a month
                                        week_data = []
                                        for weekday in range(7):  # 7 days in a week
                                            if (week == 0 and weekday < first_day_weekday) or day_count > num_days:
                                                # Empty cell
                                                week_data.append("")
                                            else:
                                                date_str = f"{month_start.year}-{month_start.month:02d}-{day_count:02d}"
                                                date = pd.Timestamp(date_str)
                                                
                                                if date in month_data.index:
                                                    week_data.append(f"{day_count} {month_data[date]}")
                                                else:
                                                    week_data.append(f"{day_count}")
                                                
                                                day_count += 1
                                        
                                        calendar_data.append(week_data)
                                    
                                    # Only include weeks that have days
                                    calendar_data = [week for week in calendar_data if any(cell != "" for cell in week)]
                                    
                                    # Create DataFrame for display
                                    calendar_df = pd.DataFrame(calendar_data, columns=day_names)
                                    
                                    # Display as a styled table
                                    def style_calendar(val):
                                        if "✅" in val:
                                            return 'background-color: #c8e6c9; font-weight: bold'
                                        elif "❌" in val:
                                            return 'background-color: #ffcdd2; font-weight: bold'
                                        elif "⚠️" in val:
                                            return 'background-color: #fff9c4; font-weight: bold'
                                        else:
                                            return ''
                                    
                                    # Apply the styling
                                    styled_calendar = calendar_df.style.applymap(style_calendar)
                                    st.dataframe(styled_calendar, use_container_width=True, hide_index=True)
                                
                                # Detailed attendance list
                                st.markdown("### Detailed Attendance List")
                                
                                # Sort by date (newest first) and format date column
                                df_report = df_report.sort_values("Date", ascending=False)
                                df_report["Date"] = df_report["Date"].dt.strftime("%Y-%m-%d")
                                
                                # Display as a styled dataframe
                                def style_status(val):
                                    if val == "✅":
                                        return 'color: #4caf50; font-weight: bold'
                                    else:
                                        return 'color: #f44336; font-weight: bold'
                                
                                # Apply the styling
                                styled_df = df_report.style.applymap(
                                    style_status, 
                                    subset=pd.IndexSlice[:, ['Status']]
                                )
                                
                                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                                
                                # Export to Excel
                                excel_path = os.path.join("excel_exports", f"Student_Report_{selected_roll_no}.xlsx")
                                try:
                                    # Using context manager to ensure the file is properly closed
                                    with pd.ExcelWriter(excel_path, mode='w') as writer:
                                        df_report.to_excel(writer, index=False)
                                    
                                    with open(excel_path, "rb") as file:
                                        st.download_button(
                                            label="Download Excel Report",
                                            data=file,
                                            file_name=f"Attendance_Report_{selected_roll_no}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                                    
                                    # Export to Google Sheets in parallel
                                    if sheets_available:
                                        try:
                                            worksheet_name = f"Student_Report_{selected_roll_no}"
                                            if export_to_sheets(df_report, worksheet_name):
                                                sheets_info = get_spreadsheet_info()
                                                if sheets_info and sheets_info.get('url'):
                                                    st.success(f"✅ Student report exported to Google Sheets")
                                                    st.info(f"📊 [Open Google Sheet]({sheets_info['url']})")
                                                else:
                                                    st.success(f"✅ Student report also exported to Google Sheets")
                                            else:
                                                logger.warning(f"Google Sheets export failed for student {selected_roll_no}, but Excel export succeeded")
                                        except Exception as sheets_error:
                                            logger.error(f"Error exporting student report to Google Sheets: {str(sheets_error)}")
                                except Exception as e:
                                    logger.error(f"Error exporting student report to Excel: {str(e)}")
                                    st.error(f"Failed to export report: {str(e)}")
                            else:
                                st.info("No detailed attendance records found for this student.")
                                
                except IndexError:
                    logger.error(f"Student with roll number {selected_roll_no} not found in DataFrame")
                    st.error(f"Student with roll number {selected_roll_no} not found in the student database. This may happen if the student record was deleted after the page loaded.")
                except Exception as e:
                    logger.error(f"Error retrieving student details: {str(e)}")
                    st.error(f"Failed to retrieve student details: {str(e)}")
            else:
                st.warning("No students match your search criteria.")
    
    except Exception as e:
        logger.error(f"Error generating student report: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error: {str(e)}")

elif page == "Edit Attendance":
    # Check permission
    if not can_access_feature(user, 'edit_attendance'):
        st.error("❌ Access Denied: You do not have permission to edit attendance.")
        st.info("Only HOD and Class Teachers can edit attendance records.")
    else:
        st.title("🔄 Edit Attendance")
    st.markdown('<div class="dashboard-card"><p>View and edit previous attendance records.</p></div>', unsafe_allow_html=True)
    
    # Create columns for form inputs
    col1, col2, col3 = st.columns(3)
    
    # Get subjects from database with error handling
    try:
        subjects = get_subjects()
        subject_options = [subject[1] for subject in subjects]  # Use code instead of full name
        
        with col1:
            if subject_options:
                selected_subject = st.selectbox("Select Subject", subject_options)
                subject_id = next((subject[0] for subject in subjects if subject[1] == selected_subject), None)
            else:
                st.warning("No subjects found in database. Please check database configuration.")
                selected_subject = None
                subject_id = None
        
        with col2:
            # Date selection
            report_date = st.date_input("Select Date", value=datetime.date.today())
        
        with col3:
            periods = [
                "10:15 - 11:15",
                "11:15 - 12:15",
                "01:15 - 02:15",
                "02:15 - 03:15",
                "03:30 - 04:30",
                "04:30 - 05:30"
            ]
            selected_period = st.selectbox("Select Period", periods)
        
        # Load attendance data if all parameters are selected
        if subject_id:
            # Get attendance data
            attendance_data = get_attendance_report(subject_id, report_date.strftime("%Y-%m-%d"))
            
            if attendance_data:
                st.subheader(f"Attendance for {selected_subject} on {report_date}")
                
                # Convert to dataframe and add checkbox for editing
                attendance_df = pd.DataFrame(
                    [(data[0], data[1], data[2], data[3], data[4]) for data in attendance_data],
                    columns=["ID", "Roll No", "Name", "Email", "Status"]
                )
                
                # Display attendance statistics
                present_count = sum(attendance_df["Status"] == "present")
                absent_count = sum(attendance_df["Status"] == "absent")
                total_count = len(attendance_df)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Students", str(total_count))
                with col2:
                    st.metric("Present", str(present_count))
                with col3:
                    st.metric("Absent", str(absent_count))
                with col4:
                    attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0
                    st.metric("Attendance %", f"{attendance_percentage:.1f}%")
                
                # Create a form to allow editing
                with st.form(key=f"edit_attendance_{subject_id}_{report_date}"):
                    st.markdown("### Edit Attendance Status")
                    st.markdown("Check the boxes for students who are **present**, uncheck for **absent** students.")
                    
                    # Create attendance edit options
                    attendance_status = {}
                    
                    for _, row in attendance_df.iterrows():
                        student_id = row["ID"]
                        roll_no = row["Roll No"]
                        name = row["Name"]
                        is_present = row["Status"] == "present"
                        
                        attendance_status[student_id] = st.checkbox(
                            f"{roll_no} - {name}",
                            value=is_present,
                            key=f"attendance_{student_id}"
                        )
                    
                    # Submit button
                    submit = st.form_submit_button("Update Attendance")
                    
                    if submit:
                        try:
                            update_count = 0
                            
                            for student_id, is_present in attendance_status.items():
                                status = "present" if is_present else "absent"
                                
                                # Use mark_attendance function which handles email sending
                                success = mark_attendance(
                                    student_id, 
                                    subject_id, 
                                    report_date.strftime("%Y-%m-%d"), 
                                    selected_period,
                                    status=status
                                )
                                
                                if success:
                                    update_count += 1
                            
                            st.success(f"Successfully updated attendance for {update_count} students! Emails have been sent to students.")
                            
                            # Add button to refresh the page
                            st.button("Refresh", key="refresh_attendance")
                            
                        except Exception as e:
                            logger.error(f"Error updating attendance: {str(e)}")
                            st.error(f"Failed to update attendance: {str(e)}")
                
            else:
                st.info(f"No attendance records found for {selected_subject} on {report_date}. You can create a new attendance record.")
                
                # Allow creating new attendance record manually
                with st.form(key=f"new_attendance_{subject_id}_{report_date}"):
                    st.markdown("### Create New Attendance Record")
                    st.markdown("Check the boxes for students who are **present**.")
                    
                    # Get all students enrolled in the subject
                    all_students = get_students_by_subject(subject_id)
                    
                    if not all_students:
                        st.warning("No students enrolled in this subject.")
                    else:
                        # Create attendance options
                        attendance_status = {}
                        
                        for student in all_students:
                            student_id = student["id"]
                            roll_no = student["roll_no"]
                            name = student["name"]
                            
                            attendance_status[student_id] = st.checkbox(
                                f"{roll_no} - {name}",
                                value=False,
                                key=f"new_attendance_{student_id}"
                            )
                        
                        # Submit button
                        submit = st.form_submit_button("Save Attendance")
                        
                        if submit:
                            try:
                                success_count = 0
                                
                                for student_id, is_present in attendance_status.items():
                                    if is_present:
                                        mark_attendance(student_id, subject_id, report_date.strftime("%Y-%m-%d"), selected_period)
                                        success_count += 1
                                
                                st.success(f"Successfully created attendance record with {success_count} present students!")
                                
                                # Add button to refresh the page
                                st.button("Refresh", key="refresh_new_attendance")
                                
                            except Exception as e:
                                logger.error(f"Error creating attendance: {str(e)}")
                                st.error(f"Failed to create attendance: {str(e)}")
        else:
            st.info("Please select a subject, date, and period to view or edit attendance.")
    
    except Exception as e:
        logger.error(f"Error in Edit Attendance page: {str(e)}\n{traceback.format_exc()}")
        st.error(f"Error: {str(e)}")

elif page == "Email Settings":
    # Check permission - Only HOD can access
    if not can_access_feature(user, 'manage_users'):
        st.error("❌ Access Denied: You do not have permission to access Email Settings.")
        st.info("Only HOD can configure email settings.")
    else:
        st.title("📧 Email Settings")
        st.markdown('<div class="dashboard-card"><p>Configure email notifications for attendance marking.</p></div>', unsafe_allow_html=True)
        
        try:
            from utils.email_utils import test_email_configuration
            from config import (
                EMAIL_ENABLED,
                SMTP_SERVER,
                SMTP_PORT,
                SMTP_USERNAME,
                SMTP_PASSWORD,
                EMAIL_FROM,
                EMAIL_SEND_ON_PRESENT,
                EMAIL_SEND_ON_ABSENT
            )
            
            st.markdown("### Email Configuration")
            st.info("⚠️ **Note:** Email settings are configured via environment variables. To change these settings, update your environment variables or modify the `config.py` file and restart the application.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Current Settings")
                st.write(f"**Email Enabled:** {'✅ Yes' if EMAIL_ENABLED else '❌ No'}")
                st.write(f"**SMTP Server:** {SMTP_SERVER}")
                st.write(f"**SMTP Port:** {SMTP_PORT}")
                st.write(f"**From Address:** {EMAIL_FROM}")
                st.write(f"**Send on Present:** {'✅ Yes' if EMAIL_SEND_ON_PRESENT else '❌ No'}")
                st.write(f"**Send on Absent:** {'✅ Yes' if EMAIL_SEND_ON_ABSENT else '❌ No'}")
                
                if SMTP_USERNAME:
                    st.write(f"**SMTP Username:** {SMTP_USERNAME[:3]}***")
                else:
                    st.warning("⚠️ SMTP Username not configured")
                
                if SMTP_PASSWORD:
                    st.write("**SMTP Password:** ********")
                else:
                    st.warning("⚠️ SMTP Password not configured")
            
            with col2:
                st.markdown("#### Test Email Configuration")
                st.write("Click the button below to test your email configuration:")
                
                if st.button("🧪 Test Email Connection", use_container_width=True):
                    with st.spinner("Testing email configuration..."):
                        success, message = test_email_configuration()
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                
                st.markdown("---")
                st.markdown("#### Email Notification Settings")
                st.info("""
                **How Email Notifications Work:**
                - When attendance is marked (present or absent), an email is automatically sent to the student
                - Emails include: Subject name, Date, Period, Roll Number, and Status
                - Students receive a nicely formatted HTML email with their attendance status
                - Email sending failures won't prevent attendance from being saved
                """)
                
                st.markdown("---")
                st.markdown("#### 📋 Recent Email Logs")
                
                # Function to read recent email logs
                try:
                    log_file_path = "app.log"
                    if os.path.exists(log_file_path):
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        # Filter email-related logs (last 50 lines that contain email keywords)
                        email_logs = []
                        keywords = ['email', 'SMTP', 'smtp', 'Email', 'attendance notification']
                        for line in lines[-200:]:  # Check last 200 lines
                            if any(keyword in line for keyword in keywords):
                                email_logs.append(line.strip())
                        
                        if email_logs:
                            # Show last 30 email-related log entries
                            recent_logs = email_logs[-30:]
                            with st.expander(f"View Recent Email Logs ({len(recent_logs)} entries)", expanded=False):
                                st.code("\n".join(recent_logs), language=None)
                            
                            # Count success vs failures
                            success_count = sum(1 for log in recent_logs if '✅' in log or 'successfully' in log.lower())
                            error_count = sum(1 for log in recent_logs if '❌' in log or 'error' in log.lower() or 'failed' in log.lower())
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Recent Successes", success_count)
                            with col2:
                                st.metric("Recent Errors", error_count)
                        else:
                            st.info("No email-related logs found in recent entries.")
                            st.info("📝 **Tip:** Try sending a test email or marking attendance to generate logs.")
                    else:
                        st.warning(f"Log file not found at: {log_file_path}")
                        st.info("Logs will appear here once email operations are performed.")
                except Exception as e:
                    st.error(f"Error reading logs: {str(e)}")
                    logger.error(f"Error reading email logs: {str(e)}")
                
                st.markdown("---")
                st.markdown("#### Configuration Instructions")
                st.markdown("""
                To configure email settings, set these environment variables:
                - `EMAIL_ENABLED=true` - Enable email notifications
                - `SMTP_SERVER=smtp.gmail.com` - Your SMTP server
                - `SMTP_PORT=587` - SMTP port (usually 587 for TLS)
                - `SMTP_USERNAME=your-email@gmail.com` - Your email address
                - `SMTP_PASSWORD=your-app-password` - Your email password or app password
                - `EMAIL_FROM=attendance@example.com` - From address
                - `EMAIL_SEND_ON_PRESENT=true` - Send email when marked present
                - `EMAIL_SEND_ON_ABSENT=true` - Send email when marked absent
                
                **For Gmail:**
                1. Enable 2-Factor Authentication
                2. Generate an App Password: https://myaccount.google.com/apppasswords
                3. Use the app password as `SMTP_PASSWORD`
                
                **For Resend:**
                1. Sign up at https://resend.com
                2. Get your API key (starts with `re_`)
                3. **Verify your domain** in Resend dashboard (Settings → Domains)
                4. Use these settings:
                   - `SMTP_SERVER=smtp.resend.com`
                   - `SMTP_PORT=465` (or 587)
                   - `SMTP_USERNAME=resend`
                   - `SMTP_PASSWORD=your-api-key-here` (the full API key starting with `re_`)
                   - `EMAIL_FROM=your-verified-domain@yourdomain.com` (must use verified domain)
                5. **Critical:** The `EMAIL_FROM` address must use a domain you've verified in Resend
                   - ❌ Cannot use: `attendance@gmail.com` or `attendance@outlook.com`
                   - ✅ Must use: `attendance@yourdomain.com` (where yourdomain.com is verified)
                
                **Troubleshooting Resend Authentication Errors:**
                - ✅ Verify your API key is correct and active in Resend dashboard
                - ✅ Check that your domain is verified (Settings → Domains → Status should be "Verified")
                - ✅ Ensure `EMAIL_FROM` uses your verified domain (not Gmail/Outlook)
                - ✅ Check Resend dashboard for any API key restrictions or rate limits
                - ✅ Verify DNS records (SPF, DKIM) are properly configured for your domain
                """)
                
        except ImportError as e:
            st.error(f"Error importing email utilities: {str(e)}")
            logger.error(f"Error importing email utilities: {str(e)}")
        except Exception as e:
            logger.error(f"Error in Email Settings page: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Error: {str(e)}")

# Footer
st.sidebar.divider()
st.sidebar.info(
    "Automated Facial Attendance System\n"
    "Developed for ENTC B.Tech b"
) 