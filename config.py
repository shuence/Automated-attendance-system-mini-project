"""
Configuration management for the Attendance System.
Centralizes all configuration values and settings.
"""
import os
from typing import Dict, List
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
FACES_DIR = BASE_DIR / "faces"
EXCEL_EXPORTS_DIR = BASE_DIR / "excel_exports"
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "attendance.db"

# Application settings
APP_TITLE = "ENTC B.Tech b Facial Attendance System"
APP_ICON = "👨‍🎓"
APP_LAYOUT = "wide"

# Department, Year, Division (can be overridden via environment variables)
DEPARTMENT = os.getenv("DEPARTMENT", "ENTC")
YEAR = os.getenv("YEAR", "B.Tech")
DIVISION = os.getenv("DIVISION", "B")

# Subject code to short name mapping
SUBJECT_SHORT_NAMES: Dict[str, str] = {
    "Fiber Optic Communication": "FOC",
    "Microwave Engineering": "ME",
    "Mobile Computing ": "MC",
    "E-Waste Management": "Ewaste",
    "Data Structures and Algorithms in Java": "DSAJ",
    "Engineering Economics and Financial Management": "EEFM",
    "Microwave Engineering Lab": "ME Lab",
    "Mini Project": "Mini project"
}

# Default subjects (code, name)
DEFAULT_SUBJECTS: List[tuple] = [
    ("FOC", "Fiber Optic Communication"),
    ("ME", "Microwave Engineering"),
    ("MC", "Mobile Computing"),
    ("Ewaste", "E-Waste Management"),
    ("DSAJ", "Data Structures and Algorithms in Java"),
    ("EEFM", "Engineering Economics and Financial Management"),
    ("ME Lab", "Microwave Engineering Lab"),
    ("Mini project", "Mini Project"),
]

# ESP32-CAM defaults (can be overridden via environment variables)
ESP32_DEFAULT_URL = os.getenv("ESP32_CAM_URL", "http://192.168.137.208:8080")
ESP32_DEFAULT_USERNAME = os.getenv("ESP32_CAM_USERNAME", "admin")
ESP32_DEFAULT_PASSWORD = os.getenv("ESP32_CAM_PASSWORD", "admin")  # Should be changed in production

# DeepFace settings
DEEPFACE_MODEL = os.getenv("DEEPFACE_MODEL", "Facenet512")
DEEPFACE_THRESHOLD = float(os.getenv("DEEPFACE_THRESHOLD", "0.6"))
DEEPFACE_DETECTOR_BACKEND = os.getenv("DEEPFACE_DETECTOR", "opencv")

# Request settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "app.log"
DEEPFACE_LOG_FILE = BASE_DIR / "deepface.log"

# Email settings (can be overridden via environment variables)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.resend.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "resend")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "re_MwypuzDb_AiBGqcBYpS5MVyNrZgM8Wa73")
EMAIL_FROM = os.getenv("EMAIL_FROM", "attendance@shuence.com")
EMAIL_SEND_ON_PRESENT = os.getenv("EMAIL_SEND_ON_PRESENT", "true").lower() == "true"
EMAIL_SEND_ON_ABSENT = os.getenv("EMAIL_SEND_ON_ABSENT", "true").lower() == "true"

# Google Sheets settings (can be overridden via environment variables)
GOOGLE_SHEETS_ENABLED = os.getenv("GOOGLE_SHEETS_ENABLED", "false").lower() == "true"
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", str(BASE_DIR / "google_credentials.json"))
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_SHEETS_FOLDER_ID = os.getenv("GOOGLE_SHEETS_FOLDER_ID", "")  # Optional: folder to create sheets in
GOOGLE_SHEETS_SHARE_EMAIL = os.getenv("GOOGLE_SHEETS_SHARE_EMAIL", "shubhampitekar2323@gmail.com")  # Email to share sheets with

# Create necessary directories
FACES_DIR.mkdir(exist_ok=True)
EXCEL_EXPORTS_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

