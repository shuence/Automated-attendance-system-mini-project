"""
Email utilities for sending attendance notifications to students.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Email configuration - imported from config
try:
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
except ImportError:
    # Fallback to environment variables if config not available
    import os
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "attendance@example.com")
    EMAIL_SEND_ON_PRESENT = os.getenv("EMAIL_SEND_ON_PRESENT", "true").lower() == "true"
    EMAIL_SEND_ON_ABSENT = os.getenv("EMAIL_SEND_ON_ABSENT", "true").lower() == "true"

def send_attendance_email(
    student_email: str,
    student_name: str,
    subject_name: str,
    date: str,
    period: str,
    status: str,
    roll_no: str
) -> bool:
    """
    Send attendance notification email to a student.
    
    Args:
        student_email: Student's email address
        student_name: Student's name
        subject_name: Subject name
        date: Attendance date
        period: Period/time
        status: 'present' or 'absent'
        roll_no: Student roll number
        
    Returns:
        True if email sent successfully, False otherwise
    """
    logger.info(f"Attempting to send email to {student_email} for {student_name} ({roll_no}) - {status}")
    
    if not EMAIL_ENABLED:
        logger.warning(f"EMAIL_ENABLED is False. Email disabled. Would send to {student_email}: {status} for {subject_name}")
        return False
    
    if not student_email or not student_email.strip():
        logger.warning(f"No email address for student {student_name} ({roll_no})")
        return False
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.error(f"SMTP credentials not configured. SMTP_USERNAME: {'SET' if SMTP_USERNAME else 'NOT SET'}, SMTP_PASSWORD: {'SET' if SMTP_PASSWORD else 'NOT SET'}")
        return False
    
    logger.info(f"Email config check passed. Using SMTP server: {SMTP_SERVER}:{SMTP_PORT}, From: {EMAIL_FROM}")
    
    try:
        logger.info(f"Creating email message for {student_email}")
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_FROM
        msg['To'] = student_email
        msg['Subject'] = f"Attendance Marked - {subject_name} ({date})"
        
        logger.debug(f"Email subject: {msg['Subject']}")
        
        # Email body
        status_text = "Present ✅" if status == "present" else "Absent ❌"
        status_color = "#4caf50" if status == "present" else "#f44336"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
              <h2 style="color: #1E3A8A;">📚 Attendance Notification</h2>
              
              <p>Dear <strong>{student_name}</strong>,</p>
              
              <p>Your attendance has been marked for the following class:</p>
              
              <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Subject:</strong> {subject_name}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Period:</strong> {period}</p>
                <p><strong>Roll Number:</strong> {roll_no}</p>
                <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold; font-size: 18px;">{status_text}</span></p>
              </div>
              
              <p>If you believe there is an error in your attendance record, please contact your class teacher or HOD.</p>
              
              <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
              
              <p style="color: #666; font-size: 12px;">
                This is an automated email from the Facial Attendance System.<br>
                Please do not reply to this email.
              </p>
            </div>
          </body>
        </html>
        """
        
        text_body = f"""
Attendance Notification

Dear {student_name},

Your attendance has been marked for the following class:

Subject: {subject_name}
Date: {date}
Period: {period}
Roll Number: {roll_no}
Status: {status_text}

If you believe there is an error in your attendance record, please contact your class teacher or HOD.

---
This is an automated email from the Facial Attendance System.
Please do not reply to this email.
        """
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        logger.info(f"Using credentials - Username: {SMTP_USERNAME}, Password length: {len(SMTP_PASSWORD) if SMTP_PASSWORD else 0} chars")
        
        # Send email
        try:
            # Use SMTP_SSL for port 465 (SSL), SMTP with starttls for port 587 (TLS)
            if SMTP_PORT == 465:
                logger.info(f"Using SSL connection (port 465)")
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    logger.info(f"SSL connection established. Attempting login...")
                    
                    # For Resend, try different authentication methods
                    auth_success = False
                    auth_error = None
                    
                    # Method 1: Standard login
                    try:
                        server.login(SMTP_USERNAME, SMTP_PASSWORD)
                        auth_success = True
                        logger.info(f"SMTP login successful with standard method")
                    except smtplib.SMTPAuthenticationError as e:
                        auth_error = str(e)
                        logger.warning(f"Standard authentication failed: {str(e)}")
                        
                        # Method 2: For Resend, try using API key as username
                        if "resend.com" in SMTP_SERVER.lower():
                            logger.info(f"Trying Resend-specific authentication (API key as username)...")
                            try:
                                # Resend sometimes uses API key as both username and password
                                server.login(SMTP_PASSWORD, SMTP_PASSWORD)
                                auth_success = True
                                logger.info(f"SMTP login successful with Resend API key method")
                            except smtplib.SMTPAuthenticationError as e2:
                                logger.warning(f"Resend API key method also failed: {str(e2)}")
                                auth_error = str(e2)
                    
                    if not auth_success:
                        raise smtplib.SMTPAuthenticationError(535, auth_error or "Authentication failed")
                    
                    logger.info(f"Sending message to {student_email}...")
                    server.send_message(msg)
                    logger.info(f"✅ Email sent successfully to {student_email} for {student_name} ({roll_no}) - {status}")
                    return True
            else:
                logger.info(f"Using STARTTLS connection (port {SMTP_PORT})")
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    logger.info(f"SMTP connection established. Starting TLS...")
                    server.starttls()
                    logger.info(f"TLS started. Attempting login...")
                    
                    # For Resend, try different authentication methods
                    auth_success = False
                    auth_error = None
                    
                    # Method 1: Standard login
                    try:
                        server.login(SMTP_USERNAME, SMTP_PASSWORD)
                        auth_success = True
                        logger.info(f"SMTP login successful with standard method")
                    except smtplib.SMTPAuthenticationError as e:
                        auth_error = str(e)
                        logger.warning(f"Standard authentication failed: {str(e)}")
                        
                        # Method 2: For Resend, try using API key as username
                        if "resend.com" in SMTP_SERVER.lower():
                            logger.info(f"Trying Resend-specific authentication (API key as username)...")
                            try:
                                server.login(SMTP_PASSWORD, SMTP_PASSWORD)
                                auth_success = True
                                logger.info(f"SMTP login successful with Resend API key method")
                            except smtplib.SMTPAuthenticationError as e2:
                                logger.warning(f"Resend API key method also failed: {str(e2)}")
                                auth_error = str(e2)
                    
                    if not auth_success:
                        raise smtplib.SMTPAuthenticationError(535, auth_error or "Authentication failed")
                    
                    logger.info(f"Sending message to {student_email}...")
                    server.send_message(msg)
                    logger.info(f"✅ Email sent successfully to {student_email} for {student_name} ({roll_no}) - {status}")
                    return True
        except smtplib.SMTPAuthenticationError as e:
            error_msg = str(e)
            logger.error(f"❌ SMTP authentication failed. Error: {error_msg}")
            
            # Provide specific guidance based on SMTP server
            if "resend.com" in SMTP_SERVER.lower():
                logger.error(f"   Resend SMTP Configuration:")
                logger.error(f"   - Username should be: 'resend'")
                logger.error(f"   - Password should be: Your Resend API key (starts with 're_')")
                logger.error(f"   - Make sure your API key is valid and has SMTP access enabled")
                logger.error(f"   - Verify your API key at: https://resend.com/api-keys")
                logger.error(f"   - Check that your domain is verified in Resend dashboard")
            else:
                logger.error(f"   Check your SMTP_USERNAME and SMTP_PASSWORD in config")
                logger.error(f"   - Username: {SMTP_USERNAME}")
                logger.error(f"   - Password length: {len(SMTP_PASSWORD) if SMTP_PASSWORD else 0} characters")
                logger.error(f"   - Make sure credentials are correct and account is not locked")
            
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ Failed to connect to SMTP server {SMTP_SERVER}:{SMTP_PORT}. Error: {str(e)}")
            logger.error(f"   Check your SMTP_SERVER and SMTP_PORT settings")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error sending email to {student_email}: {str(e)}")
            logger.error(f"   SMTP error code: {getattr(e, 'smtp_code', 'N/A')}, Error: {getattr(e, 'smtp_error', str(e))}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email to {student_email}: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False

def send_bulk_attendance_emails(
    attendance_records: List[Dict],
    subject_name: str,
    date: str,
    period: str
) -> Dict[str, int]:
    """
    Send attendance notification emails to multiple students.
    
    Args:
        attendance_records: List of dictionaries with student info and status
            Each dict should have: email, name, roll_no, status
        subject_name: Subject name
        date: Attendance date
        period: Period/time
        
    Returns:
        Dictionary with 'sent' and 'failed' counts
    """
    logger.info(f"Starting bulk email send for {len(attendance_records)} students")
    logger.info(f"Subject: {subject_name}, Date: {date}, Period: {period}")
    logger.info(f"Email enabled: {EMAIL_ENABLED}, SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
    
    results = {'sent': 0, 'failed': 0, 'details': []}
    
    for idx, record in enumerate(attendance_records, 1):
        student_email = record.get('email')
        student_name = record.get('name', 'Student')
        roll_no = record.get('roll_no', '')
        status = record.get('status', 'absent')
        
        logger.info(f"[{idx}/{len(attendance_records)}] Processing email for {student_name} ({roll_no}) - {student_email}")
        
        success = send_attendance_email(
            student_email=student_email,
            student_name=student_name,
            subject_name=subject_name,
            date=date,
            period=period,
            status=status,
            roll_no=roll_no
        )
        
        if success:
            results['sent'] += 1
            results['details'].append({'email': student_email, 'name': student_name, 'status': 'sent'})
            logger.info(f"✅ [{idx}/{len(attendance_records)}] Email sent successfully to {student_email}")
        else:
            results['failed'] += 1
            results['details'].append({'email': student_email, 'name': student_name, 'status': 'failed'})
            logger.error(f"❌ [{idx}/{len(attendance_records)}] Failed to send email to {student_email}")
    
    logger.info(f"Bulk email send completed. Sent: {results['sent']}, Failed: {results['failed']}")
    return results

def test_email_configuration() -> tuple[bool, str]:
    """
    Test email configuration by attempting to connect to SMTP server.
    
    Returns:
        Tuple of (success, message)
    """
    if not EMAIL_ENABLED:
        return False, "Email is disabled. Set EMAIL_ENABLED=true to enable."
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False, "SMTP credentials not configured. Please set SMTP_USERNAME and SMTP_PASSWORD."
    
    try:
        # Use SMTP_SSL for port 465 (SSL), SMTP with starttls for port 587 (TLS)
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                # Try standard login first
                try:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                except smtplib.SMTPAuthenticationError:
                    # For Resend, try API key as both username and password
                    if "resend.com" in SMTP_SERVER.lower():
                        server.login(SMTP_PASSWORD, SMTP_PASSWORD)
                    else:
                        raise
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                # Try standard login first
                try:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                except smtplib.SMTPAuthenticationError:
                    # For Resend, try API key as both username and password
                    if "resend.com" in SMTP_SERVER.lower():
                        server.login(SMTP_PASSWORD, SMTP_PASSWORD)
                    else:
                        raise
        return True, "Email configuration is valid and connection successful!"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Please check your username and password."
    except smtplib.SMTPException as e:
        return False, f"SMTP connection error: {str(e)}"
    except Exception as e:
        return False, f"Error testing email configuration: {str(e)}"

