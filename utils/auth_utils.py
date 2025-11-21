"""
Authentication utilities for the Attendance System.
Handles user login, logout, and role-based access control.
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Tuple
from utils.db_utils import get_connection, get_db_connection

logger = logging.getLogger(__name__)

# Role definitions and permissions
ROLES = {
    'HOD': {
        'name': 'Head of Department',
        'permissions': [
            'view_all_reports',
            'edit_attendance',
            'manage_students',
            'manage_users',
            'view_analytics',
            'export_data',
            'take_attendance',
            'view_class_reports'
        ]
    },
    'Class Teacher': {
        'name': 'Class Teacher',
        'permissions': [
            'view_all_reports',
            'edit_attendance',
            'manage_students',
            'view_analytics',
            'export_data',
            'take_attendance',
            'view_class_reports'
        ]
    },
    'Teacher': {
        'name': 'Teacher',
        'permissions': [
            'take_attendance',
            'view_class_reports',
            'view_analytics'
        ]
    }
}


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    return hash_password(password) == password_hash


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        User dictionary if authentication successful, None otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, role, name, email, department, is_active
                FROM users
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            
            if user is None:
                logger.warning(f"Authentication failed: User '{username}' not found or inactive")
                return None
            
            # Verify password
            if not verify_password(password, user['password_hash']):
                logger.warning(f"Authentication failed: Invalid password for user '{username}'")
                return None
            
            # Update last login
            cursor.execute('''
                UPDATE users
                SET last_login = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), user['id']))
            
            # Convert to dictionary
            user_dict = {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'name': user['name'],
                'email': user['email'],
                'department': user['department'],
                'permissions': ROLES.get(user['role'], {}).get('permissions', [])
            }
            
            logger.info(f"User '{username}' authenticated successfully as {user['role']}")
            return user_dict
            
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}")
        return None


def create_user(username: str, password: str, role: str, name: str, 
                email: Optional[str] = None, department: str = 'ENTC') -> Tuple[bool, Optional[str]]:
    """
    Create a new user.
    
    Args:
        username: Username (must be unique)
        password: Plain text password
        role: User role ('HOD', 'Class Teacher', or 'Teacher')
        name: Full name
        email: Email address (optional)
        department: Department name
        
    Returns:
        Tuple of (success, error_message)
    """
    if role not in ROLES:
        return False, f"Invalid role. Must be one of: {', '.join(ROLES.keys())}"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return False, f"Username '{username}' already exists"
            
            # Hash password
            password_hash = hash_password(password)
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, name, email, department)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, role, name, email, department))
            
            logger.info(f"User '{username}' created successfully with role '{role}'")
            return True, None
            
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return False, f"Error creating user: {str(e)}"


def update_user_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Update a user's password.
    
    Args:
        user_id: User ID
        old_password: Current password
        new_password: New password
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user is None:
                return False, "User not found"
            
            # Verify old password
            if not verify_password(old_password, user['password_hash']):
                return False, "Current password is incorrect"
            
            # Update password
            new_password_hash = hash_password(new_password)
            cursor.execute('''
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            ''', (new_password_hash, user_id))
            
            logger.info(f"Password updated for user ID {user_id}")
            return True, None
            
    except Exception as e:
        logger.error(f"Error updating password: {str(e)}")
        return False, f"Error updating password: {str(e)}"


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user information by ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, role, name, email, department, is_active, last_login
                FROM users
                WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'name': user['name'],
                    'email': user['email'],
                    'department': user['department'],
                    'is_active': bool(user['is_active']),
                    'last_login': user['last_login'],
                    'permissions': ROLES.get(user['role'], {}).get('permissions', [])
                }
            return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None


def get_all_users() -> list:
    """Get all users (for admin management)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, role, name, email, department, is_active, last_login, created_at
                FROM users
                ORDER BY role, username
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row['id'],
                    'username': row['username'],
                    'role': row['role'],
                    'name': row['name'],
                    'email': row['email'],
                    'department': row['department'],
                    'is_active': bool(row['is_active']),
                    'last_login': row['last_login'],
                    'created_at': row['created_at']
                })
            return users
    except Exception as e:
        logger.error(f"Error getting all users: {str(e)}")
        return []


def has_permission(user: Dict, permission: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: User dictionary (must have 'permissions' key)
        permission: Permission name to check
        
    Returns:
        True if user has permission, False otherwise
    """
    if not user or 'permissions' not in user:
        return False
    return permission in user.get('permissions', [])


def can_access_feature(user: Dict, feature: str) -> bool:
    """
    Check if a user can access a specific feature based on their role.
    
    Args:
        user: User dictionary
        feature: Feature name (e.g., 'manage_students', 'edit_attendance')
        
    Returns:
        True if user can access feature, False otherwise
    """
    return has_permission(user, feature)

