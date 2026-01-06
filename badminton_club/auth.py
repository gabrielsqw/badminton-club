"""
Authentication module for the badminton club application.

This module handles user authentication, password verification, and session management
using a PostgreSQL database backend with SQLAlchemy.
"""

import logging
import os
import hashlib
import secrets
from typing import Optional
from flask import session
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from badminton_club.database import db_session
from badminton_club.database.models import User

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles authentication logic for the application."""

    def __init__(self):
        """Initialize the authentication manager."""
        self.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username from the database."""
        try:
            return db_session.query(User).filter(
                User.username == username,
                User.is_active == True  # noqa: E712
            ).first()
        except OperationalError as e:
            # Database connection issues (not initialized, unavailable)
            logger.debug("Database unavailable: %s", e)
            return None
        except SQLAlchemyError as e:
            # Other database errors
            logger.error("Database error while fetching user: %s", e)
            return None

    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verify username and password against database.

        Args:
            username: The username to verify
            password: The password to verify (plaintext)

        Returns:
            True if credentials are valid, False otherwise
        """
        if not username or not password:
            return False

        user = self.get_user_by_username(username)
        if user is None:
            # Fall back to environment-based auth if DB not available
            return self._verify_fallback_credentials(username, password)

        return user.check_password(password)

    def _verify_fallback_credentials(self, username: str, password: str) -> bool:
        """Fallback authentication using environment variables."""
        env_username = os.environ.get('ADMIN_USERNAME', 'admin')
        env_hash = os.environ.get('ADMIN_PASSWORD_HASH')

        if not env_hash:
            # Default password: 'password123'
            env_hash = hashlib.sha256('password123'.encode()).hexdigest()

        # Use constant-time comparison for username too
        username_match = secrets.compare_digest(username, env_username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        password_match = secrets.compare_digest(password_hash, env_hash)

        return username_match and password_match

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

    def create_user(self, username: str, password: str, email: str = None) -> Optional[User]:
        """
        Create a new user in the database.

        Args:
            username: The username for the new user
            password: The password for the new user (plaintext)
            email: Optional email address

        Returns:
            The created User object, or None if creation failed
        """
        try:
            user = User.create_user(username=username, password=password, email=email)
            db_session.add(user)
            db_session.commit()
            return user
        except SQLAlchemyError as e:
            logger.error("Failed to create user '%s': %s", username, e)
            db_session.rollback()
            return None


# Global auth manager instance
auth_manager = AuthManager()
