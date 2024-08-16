import os

from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# Redis credentials
REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0",

# Postgres credentials
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
    database=DB_NAME

)