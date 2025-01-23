""" Database configuration """
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

# Get the absolute path to .env.dev
current_dir = Path(__file__).resolve().parent.parent  # Go up two levels from db/database.py to data_handler
env_path = current_dir / '.env.dev'
print(f"Looking for .env file at: {env_path}")

load_dotenv()

# Add debug prints to see what values are being loaded
# print("Environment variables:")
# print(f"DB_USER: {os.environ.get('DB_USER')}")
# print(f"DB_PASSWORD: {os.environ.get('DB_PASSWORD')}")
# print(f"DB_HOST: {os.environ.get('DB_HOST')}")
# print(f"DB_PORT: {os.environ.get('DB_PORT')}")
# print(f"DB_NAME: {os.environ.get('DB_NAME')}")

DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_SERVER = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", 5433)
DB_NAME = os.environ.get("DB_NAME", "data_handler")

SQLALCHEMY_DATABASE_URL = (f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}")

# print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_database() -> SessionLocal:
    """
    Creates the database session
    :return: SessionLocal
    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
