import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ERROR_CHAT_ID = int(os.environ.get("ERROR_CHAT_ID", 123))

REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)


REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
