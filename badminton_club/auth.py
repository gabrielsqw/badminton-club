"""
Authentication module for the badminton club application.

This module handles user authentication, password verification, and session management
with secure practices including password hashing and environment-based configuration.
"""

import os
import hashlib
import secrets
from typing import Optional
from flask import session


class AuthManager:
    """Handles authentication logic for the application."""
    
    def __init__(self):
        """Initialize the authentication manager with environment-based config."""
        self.username = os.environ.get('ADMIN_USERNAME', 'admin')
        self.password_hash = self._get_password_hash()
        self.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    def _get_password_hash(self) -> str:
        """Get the password hash from environment or use default."""
        env_hash = os.environ.get('ADMIN_PASSWORD_HASH')
        if env_hash:
            return env_hash
        
        # Default password: 'password123'
        default_password = 'password123'
        return hashlib.sha256(default_password.encode()).hexdigest()
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verify username and password against stored credentials.
        
        Args:
            username: The username to verify
            password: The password to verify (plaintext)
            
        Returns:
            True if credentials are valid, False otherwise
        """
        if not username or not password:
            return False
            
        if username != self.username:
            return False
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def login_user(self, username: str) -> None:
        """Mark the user as authenticated in the session."""
        session['authenticated'] = True
        session['username'] = username
    
    def logout_user(self) -> None:
        """Clear the user's session."""
        session.clear()
    
    def is_authenticated(self) -> bool:
        """Check if the current user is authenticated."""
        return session.get('authenticated', False)
    
    def get_current_username(self) -> Optional[str]:
        """Get the current authenticated username."""
        if self.is_authenticated():
            return session.get('username')
        return None
    
    def get_secret_key(self) -> str:
        """Get the Flask secret key for session management."""
        return self.secret_key
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password for storage.
        
        Args:
            password: The plaintext password to hash
            
        Returns:
            The SHA256 hash of the password
        """
        return hashlib.sha256(password.encode()).hexdigest()


# Global auth manager instance
auth_manager = AuthManager()