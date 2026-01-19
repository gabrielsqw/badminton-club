"""
Database models for the badminton club application.
"""

import hashlib
import secrets
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from badminton_club.database import Base


# Time slots for play recommendations (1-hour windows from 7am to 10pm)
TIME_SLOTS = [
    "07:00-08:00",
    "08:00-09:00",
    "09:00-10:00",
    "10:00-11:00",
    "11:00-12:00",
    "12:00-13:00",
    "13:00-14:00",
    "14:00-15:00",
    "15:00-16:00",
    "16:00-17:00",
    "17:00-18:00",
    "18:00-19:00",
    "19:00-20:00",
    "20:00-21:00",
    "21:00-22:00",
]


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(64), nullable=False)  # SHA256 hex digest is 64 chars
    email = Column(String(120), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to play recommendations
    recommendations = relationship(
        "PlayRecommendation", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash using constant-time comparison."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return secrets.compare_digest(self.password_hash, password_hash)

    @classmethod
    def create_user(cls, username: str, password: str, email: str = None) -> "User":
        """Factory method to create a new user with hashed password."""
        user = cls(username=username, email=email)
        user.set_password(password)
        return user


class Location(Base):
    """Badminton venue/court location."""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to recommendations
    recommendations = relationship("PlayRecommendation", back_populates="location")

    def __repr__(self):
        return f"<Location {self.name}>"


class PlayRecommendation(Base):
    """User's play availability/recommendation for a specific date, time, and location."""

    __tablename__ = "play_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    time_slot = Column(String(20), nullable=False)  # Format: "07:00-08:00"
    num_guests = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="recommendations")
    location = relationship("Location", back_populates="recommendations")

    # Unique constraint: one entry per user/date/time_slot/location combination
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "date",
            "time_slot",
            "location_id",
            name="uq_user_date_time_location",
        ),
    )

    def __repr__(self):
        return f"<PlayRecommendation {self.user_id} @ {self.date} {self.time_slot}>"
