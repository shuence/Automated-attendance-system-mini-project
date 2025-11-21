"""
Session utilities for persistent login functionality.
"""
import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Path to store session tokens
SESSION_DIR = os.path.join("db", "sessions")
SESSION_FILE = os.path.join(SESSION_DIR, "active_sessions.json")

def ensure_session_dir():
    """Ensure the session directory exists"""
    os.makedirs(SESSION_DIR, exist_ok=True)

def generate_session_token(username: str, password_hash: str) -> str:
    """Generate a unique session token"""
    timestamp = datetime.now().isoformat()
    token_string = f"{username}:{password_hash}:{timestamp}"
    return hashlib.sha256(token_string.encode()).hexdigest()

def save_session_token(username: str, user_data: Dict, remember_me: bool = False):
    """
    Save a session token for persistent login.
    
    Args:
        username: Username
        user_data: User data dictionary
        remember_me: Whether to persist across browser restarts
    """
    try:
        ensure_session_dir()
        
        # Load existing sessions
        sessions = {}
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r') as f:
                    sessions = json.load(f)
            except:
                sessions = {}
        
        # Generate token
        token = generate_session_token(username, user_data.get('id', 0))
        
        # Calculate expiration (30 days if remember_me, 1 day otherwise)
        expiration_days = 30 if remember_me else 1
        expiration = (datetime.now() + timedelta(days=expiration_days)).isoformat()
        
        # Store session
        sessions[token] = {
            'username': username,
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': expiration,
            'remember_me': remember_me
        }
        
        # Clean up expired sessions
        current_time = datetime.now()
        sessions = {
            k: v for k, v in sessions.items()
            if datetime.fromisoformat(v['expires_at']) > current_time
        }
        
        # Save sessions
        with open(SESSION_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return token
    except Exception as e:
        logger.error(f"Error saving session token: {str(e)}")
        return None

def get_session_token(token: str) -> Optional[Dict]:
    """
    Retrieve user data from a session token.
    
    Args:
        token: Session token
        
    Returns:
        User data dictionary if token is valid, None otherwise
    """
    try:
        if not os.path.exists(SESSION_FILE):
            return None
        
        with open(SESSION_FILE, 'r') as f:
            sessions = json.load(f)
        
        if token not in sessions:
            return None
        
        session = sessions[token]
        
        # Check expiration
        expiration = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expiration:
            # Remove expired session
            del sessions[token]
            with open(SESSION_FILE, 'w') as f:
                json.dump(sessions, f, indent=2)
            return None
        
        return session.get('user_data')
    except Exception as e:
        logger.error(f"Error retrieving session token: {str(e)}")
        return None

def delete_session_token(token: str):
    """Delete a session token"""
    try:
        if not os.path.exists(SESSION_FILE):
            return
        
        with open(SESSION_FILE, 'r') as f:
            sessions = json.load(f)
        
        if token in sessions:
            del sessions[token]
            
            with open(SESSION_FILE, 'w') as f:
                json.dump(sessions, f, indent=2)
    except Exception as e:
        logger.error(f"Error deleting session token: {str(e)}")

def clear_all_sessions():
    """Clear all session tokens (for security/logout all)"""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception as e:
        logger.error(f"Error clearing sessions: {str(e)}")

def get_latest_session_for_user(username: str) -> Optional[str]:
    """
    Get the latest valid session token for a specific user.
    Useful for restoring sessions.
    
    Args:
        username: Username to find session for
        
    Returns:
        Session token if found and valid, None otherwise
    """
    try:
        if not os.path.exists(SESSION_FILE):
            return None
        
        with open(SESSION_FILE, 'r') as f:
            sessions = json.load(f)
        
        current_time = datetime.now()
        
        # Find the most recent valid session for this user
        latest_token = None
        latest_time = None
        
        for token, session in sessions.items():
            if session.get('username') == username:
                expiration = datetime.fromisoformat(session['expires_at'])
                if expiration > current_time:
                    created = datetime.fromisoformat(session['created_at'])
                    if latest_time is None or created > latest_time:
                        latest_time = created
                        latest_token = token
        
        return latest_token
    except Exception as e:
        logger.error(f"Error getting latest session: {str(e)}")
        return None

def get_all_valid_sessions() -> Dict[str, Dict]:
    """
    Get all valid (non-expired) sessions.
    Returns a dictionary of token -> session data.
    """
    try:
        if not os.path.exists(SESSION_FILE):
            return {}
        
        with open(SESSION_FILE, 'r') as f:
            sessions = json.load(f)
        
        current_time = datetime.now()
        
        # Filter out expired sessions
        valid_sessions = {}
        for token, session in sessions.items():
            expiration = datetime.fromisoformat(session['expires_at'])
            if expiration > current_time:
                valid_sessions[token] = session
        
        return valid_sessions
    except Exception as e:
        logger.error(f"Error getting valid sessions: {str(e)}")
        return {}

