import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)

app = Celery(
    main="derisk",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

app.conf.beat_schedule = {
    "check-every-minute": {
        "task": "check_data_changes",
        "schedule": 60,
    },
}

from .tasks import check_data_changes
