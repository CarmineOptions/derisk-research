import requests
import logging
from celery import shared_task
logger = logging.getLogger(__name__)

@shared_task(name="check_health_ratio_level_changes")
def check_health_ratio_level_changes():
    try:
        logger.error("Run check_health_ratio_level_changes")      
        response = requests.post("http://dashboard_backend:8000/api/send-notifications")
    except Exception as e:
        logger.error("Error in check_health_ratio_level_changes", e)
       


