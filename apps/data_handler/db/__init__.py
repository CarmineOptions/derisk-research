"""
Database initialization module for the data handler application.
Provides database URL configuration and base model initialization.

This module serves as the central point for database configuration,
exposing the database URL and SQLAlchemy Base class for model inheritance.
"""

from data_handler.db.database import SQLALCHEMY_DATABASE_URL, Base

__all__ = ['SQLALCHEMY_DATABASE_URL', 'Base']