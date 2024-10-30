"""
Database configuration and connection module for the data handler application.
Provides SQLAlchemy engine setup, session management, and base configuration.

This module handles:
- Environment variable loading for database credentials
- SQLAlchemy engine and session configuration
- Database connection string construction
- Session management utilities
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Database connection configuration
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_SERVER = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", 5432)
DB_NAME = os.environ.get("DB_NAME", "")

# Construct database URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}"
)

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Configure session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for declarative models
Base = declarative_base()


def get_database() -> SessionLocal:
    """Get a database session that will be automatically closed after use.
    
    Returns:
        SessionLocal: A SQLAlchemy session object that can be used for database operations.
        The session is automatically closed when the caller is done with it.
    
    Yields:
        Generator containing the database session.
    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()