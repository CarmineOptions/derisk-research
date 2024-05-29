import asyncio
import logging

from database.crud import DBConnector
from database.models import OrderBookModel
from telegram import TelegramNotifications
from utils.fucntools import (
    calculate_difference,
    compute_health_ratio_level,
    get_all_activated_subscribers_from_db,
    update_data,
)
from utils.values import HEALTH_RATIO_LEVEL_ALERT_VALUE
from web_app.order_books.ekubo.api_connector import EkuboAPIConnector
from web_app.order_books.constants import TOKEN_MAPPING
from web_app.order_books.ekubo.main import EkuboOrderBook

from .celery_conf import app

logger = logging.getLogger(__name__)
connector = DBConnector()
notificator = TelegramNotifications(db_connector=connector)


@app.task(name="check_health_ratio_level_changes")
def check_health_ratio_level_changes():
    update_data()

    subscribers = get_all_activated_subscribers_from_db()

    for subscriber in subscribers:
        health_ratio_level = compute_health_ratio_level(
            protocol_name=subscriber.protocol_id, user_id=subscriber.id
        )

        if (
            calculate_difference(health_ratio_level, subscriber.health_ratio_level)
            <= HEALTH_RATIO_LEVEL_ALERT_VALUE
        ):
            notificator.send_notification(notification_id=subscriber.id)

    asyncio.run(notificator(is_infinity=True))


@app.task(name="ekubo_order_book")
def ekubo_order_book():
    """
    Fetch the current price and liquidity of the pair from the Ekubo API.
    """
    pool_states = EkuboAPIConnector().get_pools()
    filtered_pool_states = [
        pool_state
        for pool_state in pool_states
        if pool_state["token0"] in TOKEN_MAPPING
        and pool_state["token1"] in TOKEN_MAPPING
    ]
    for pool_state in filtered_pool_states:
        token_a = pool_state["token0"]
        token_b = pool_state["token1"]
        logging.getLogger().info(
            f"Fetching data for token pair: {token_a} and {token_b}"
        )
        try:
            order_book = EkuboOrderBook(token_a, token_b)
            order_book.fetch_price_and_liquidity()
            serialized_data = order_book.serialize()
            connector.write_to_db(OrderBookModel(**serialized_data.model_dump()))
        except Exception as exc:
            logger.info(
                f"With token pair: {token_a} and {token_b} something happened: {exc}"
            )
            continue
