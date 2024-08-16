import asyncio
import logging

from database.crud import DBConnector
from telegram import TelegramNotifications
from utils.fucntools import (
    calculate_difference,
    compute_health_ratio_level,
    get_all_activated_subscribers_from_db,
    update_data,
)
from utils.values import HEALTH_RATIO_LEVEL_ALERT_VALUE


from .celery_conf import app

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
connector = DBConnector()
notificator = TelegramNotifications(db_connector=connector)


# @app.task(name="check_health_ratio_level_changes")
# def check_health_ratio_level_changes():
#     logger.info("Checking health ratio level changes")
#     # update_data()
#     logger.info("Data updated")
#
#     subscribers = get_all_activated_subscribers_from_db()
#     logger.info(f"Found {len(subscribers)} subscribers")
#     for subscriber in subscribers:
#         health_ratio_level = compute_health_ratio_level(
#             protocol_name=subscriber.protocol_id.value, user_id=subscriber.wallet_id
#         )
#
#         # if (
#         #         calculate_difference(health_ratio_level, subscriber.health_ratio_level)
#         #         <= HEALTH_RATIO_LEVEL_ALERT_VALUE
#         # ):
#         print(f"Subscriber {subscriber.id} has health ratio level {health_ratio_level}")
#         logger.info(f"Subscriber {subscriber.id} has health ratio level {health_ratio_level}")
#         notificator.send_notification(notification_id=subscriber.id)
#     logger.info("Health ratio level changes checked")
#     asyncio.run(notificator(is_infinity=True))

@app.task(name="check_health_ratio_level_changes")
def check_health_ratio_level_changes():
    logger.info("Checking health ratio level changes")
    # update_data()
    logger.info("Data updated")

    subscribers = get_all_activated_subscribers_from_db()
    logger.info(f"Found {len(subscribers)} subscribers")

    async def process_subscriber(subscriber):
        health_ratio_level = compute_health_ratio_level(
            protocol_name=subscriber.protocol_id.value, user_id=subscriber.wallet_id
        )

        logger.info(f"Subscriber {subscriber.id} has health ratio level {health_ratio_level}")

        await notificator.send_notification(notification_id=subscriber.id)

    loop = asyncio.get_event_loop()
    tasks = [process_subscriber(subscriber) for subscriber in subscribers]
    loop.run_until_complete(asyncio.gather(*tasks))

    logger.info("Health ratio level changes checked")
    asyncio.run(notificator(is_infinity=True))


# def check_health_ratio_level_changes():
#     logger.info("Checking health ratio level changes")
#     # update_data()
#     logger.info("Data updated")
#
#     subscribers = get_all_activated_subscribers_from_db()
#     logger.info(f"Found {len(subscribers)} subscribers")
#     for subscriber in subscribers:
#         health_ratio_level = compute_health_ratio_level(
#             protocol_name=subscriber.protocol_id.value, user_id=subscriber.wallet_id
#         )
#
#         # if (
#         #         calculate_difference(health_ratio_level, subscriber.health_ratio_level)
#         #         <= HEALTH_RATIO_LEVEL_ALERT_VALUE
#         # ):
#         print(f"Subscriber {subscriber.id} has health ratio level {health_ratio_level}")
#         logger.info(f"Subscriber {subscriber.id} has health ratio level {health_ratio_level}")
#         notificator.send_notification(notification_id=subscriber.id)
#     logger.info("Health ratio level changes checked")
#     asyncio.run(notificator(is_infinity=True))
#
#
# if __name__ == "__main__":
#     check_health_ratio_level_changes()