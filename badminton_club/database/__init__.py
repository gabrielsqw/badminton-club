"""
Database module for the badminton club application.

This module provides database connection management using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

# Database URL from environment variable with fallback for development
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://badminton:badminton_secret@localhost:5432/badminton_club'
)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a configured Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a scoped session for thread safety
db_session = scoped_session(SessionLocal)

# Base class for declarative models
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """Initialize the database by creating all tables."""
    from badminton_club.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session. Use as context manager or dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
