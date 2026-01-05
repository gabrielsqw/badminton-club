"""
Database models for the badminton club application.
"""

import hashlib
import secrets
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from badminton_club.database import Base


class User(Base):
    """User model for authentication."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(64), nullable=False)  # SHA256 hex digest is 64 chars
    email = Column(String(120), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash using constant-time comparison."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return secrets.compare_digest(self.password_hash, password_hash)

    @classmethod
    def create_user(cls, username: str, password: str, email: str = None) -> 'User':
        """Factory method to create a new user with hashed password."""
        user = cls(username=username, email=email)
        user.set_password(password)
        return user
