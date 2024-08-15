import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis credentials
REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)

# Tasks settings
CHECK_DATA_CHANGES_PERIOD = int(
    os.environ.get("CHECK_DATA_CHANGES_PERIOD", 60 * 2) # FIXME 2 minutes
)  # in seconds
ORDER_BOOK_TIME_INTERVAL = int(os.environ.get("ORDER_BOOK_TIME_INTERVAL", 5))  # in seconds

app = Celery(
    main="derisk",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

app.conf.beat_schedule = {
    "check-health-ratio-level-changes": {
        "task": "check_health_ratio_level_changes",
        "schedule": CHECK_DATA_CHANGES_PERIOD,
    },
}

from .tasks import (
    check_health_ratio_level_changes,
)
