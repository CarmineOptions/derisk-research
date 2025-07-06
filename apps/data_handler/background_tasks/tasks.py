import asyncio

from ..db.base import DBConnectorAsync as DBConnector

from telegram_app.telegram.utils import TelegramNotifications
from dashboard_app.app.utils.fucntools import (
    calculate_difference,
    get_all_activated_subscribers_from_db,
    get_health_ratio_level_from_endpoint,
)
from dashboard_app.app.utils.values import HEALTH_RATIO_LEVEL_ALERT_VALUE

from celery_conf import app

from dashboard_app.app.core.config import settings

connector = DBConnector(db_url=settings.database_url)
notificator = TelegramNotifications(db_connector=connector)


@app.task(name="check_health_ratio_level_changes")
def check_health_ratio_level_changes():
    print('#check_health_ratio_level_changes')
    # subscribers = get_all_activated_subscribers_from_db()

    # for subscriber in subscribers:
    #     health_ratio_level = get_health_ratio_level_from_endpoint(
    #         protocol_id=subscriber.protocol_id.value, user_id=subscriber.wallet_id
    #     )

    #     if (
    #         calculate_difference(health_ratio_level, subscriber.health_ratio_level)
    #         >= HEALTH_RATIO_LEVEL_ALERT_VALUE
    #     ):
    #         asyncio.run(notificator.send_notification(notification_id=subscriber.id))

    # asyncio.run(notificator(is_infinity=True))
