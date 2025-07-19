import os

from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
X_TELEGRAM_BOT_API_SECRET_TOKEN = os.getenv("X_TELEGRAM_BOT_API_SECRET_TOKEN")
ENV = os.getenv("ENV")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_SERVER = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", 5432)
DB_NAME = os.environ.get("DB_NAME", "")

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_SERVER,
    port=DB_PORT,
    database=DB_NAME,
)
