"""
This module initializes the database connection and imports necessary components.

It imports:
- `SQLALCHEMY_DATABASE_URL`: The URL for the SQLAlchemy database connection.
- `Base`: The declarative base class for SQLAlchemy models.
"""

from apps.data_handler.db.database import SQLALCHEMY_DATABASE_URL, Base
