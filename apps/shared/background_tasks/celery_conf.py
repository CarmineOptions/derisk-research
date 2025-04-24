import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis credentials
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)

# Tasks settings
CHECK_DATA_CHANGES_PERIOD = int(
    os.environ.get("CHECK_DATA_CHANGES_PERIOD", 60 * 30)
)  # in seconds

app = Celery(
    main="derisk",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

app.conf.beat_schedule = {
    "check-health-ratio-level-changes": {
        "task": "apps.shared.background_tasks.tasks.check_health_ratio_level_changes",
        "schedule": CHECK_DATA_CHANGES_PERIOD,
    },
}

# Import the task from the updated location
# from shared.background_tasks.tasks import check_health_ratio_level_changes