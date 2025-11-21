"""
Input validation utilities for the Attendance System.
"""
import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional, Tuple


def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an IP address.
    
    Args:
        ip: IP address string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ip or not ip.strip():
        return False, "IP address cannot be empty"
    
    try:
        ipaddress.ip_address(ip.strip())
        return True, None
    except ValueError:
        return False, f"'{ip}' is not a valid IP address"


def validate_url(url: str, require_http: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL.
    
    Args:
        url: URL string to validate
        require_http: Whether to require http/https scheme
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL cannot be empty"
    
    try:
        parsed = urlparse(url.strip())
        
        if require_http and parsed.scheme not in ['http', 'https']:
            return False, "URL must start with http:// or https://"
        
        if not parsed.netloc:
            return False, "URL must include a hostname or IP address"
        
        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_roll_number(roll_no: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a student roll number.
    
    Args:
        roll_no: Roll number string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not roll_no or not roll_no.strip():
        return False, "Roll number cannot be empty"
    
    roll_no = roll_no.strip()
    
    # Allow alphanumeric with common separators
    if not re.match(r'^[A-Za-z0-9\-_]+$', roll_no):
        return False, "Roll number can only contain letters, numbers, hyphens, and underscores"
    
    if len(roll_no) < 2:
        return False, "Roll number must be at least 2 characters"
    
    if len(roll_no) > 20:
        return False, "Roll number must be 20 characters or less"
    
    return True, None


def validate_email(email: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate an email address (optional field).
    
    Args:
        email: Email string to validate (can be None/empty)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or not email.strip():
        return True, None  # Email is optional
    
    email = email.strip()
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 100:
        return False, "Email address is too long (max 100 characters)"
    
    return True, None


def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a student name.
    
    Args:
        name: Name string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name must be 100 characters or less"
    
    # Allow letters, spaces, hyphens, apostrophes, and common name characters
    if not re.match(r'^[A-Za-z\s\-\'\.]+$', name):
        return False, "Name can only contain letters, spaces, hyphens, apostrophes, and periods"
    
    return True, None


def validate_esp32_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ESP32-CAM URL.
    
    Args:
        url: ESP32-CAM URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, error = validate_url(url, require_http=True)
    
    if not is_valid:
        return is_valid, error
    
    # Additional checks for ESP32-CAM
    parsed = urlparse(url.strip())
    
    # Check if it's a local network address (optional, just a warning)
    host = parsed.hostname
    if host:
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_global:  # Not a private IP
                return True, "Warning: Using a public IP address. Ensure this is intentional."
        except ValueError:
            pass  # Hostname, not IP
    
    return True, None

