import asyncio

from database.crud import DBConnector
from telegram import TelegramNotifications
from utils.fucntools import (
    calculate_difference,
    get_health_ratio_level_from_endpoint,
    get_all_activated_subscribers_from_db,
)
from utils.values import HEALTH_RATIO_LEVEL_ALERT_VALUE

from .celery_conf import app


connector = DBConnector()
notificator = TelegramNotifications(db_connector=connector)


@app.task(name="check_health_ratio_level_changes")
def check_health_ratio_level_changes():
    subscribers = get_all_activated_subscribers_from_db()

    for subscriber in subscribers:
        health_ratio_level = get_health_ratio_level_from_endpoint(
            protocol_id=subscriber.protocol_id.value, user_id=subscriber.wallet_id
        )

        if (calculate_difference(health_ratio_level, subscriber.health_ratio_level)
            >= HEALTH_RATIO_LEVEL_ALERT_VALUE
        ):
            asyncio.run(notificator.send_notification(notification_id=subscriber.id))

    asyncio.run(notificator(is_infinity=True))

# FIXME Should I remove this code?
# @app.task(name="ekubo_order_book")
# def ekubo_order_book():
#     """
#     Fetch the current price and liquidity of the pair from the Ekubo API.
#     """
#     pool_states = EkuboAPIConnector().get_pools()
#     filtered_pool_states = [
#         pool_state
#         for pool_state in pool_states
#         if pool_state["token0"] in TOKEN_MAPPING
#         and pool_state["token1"] in TOKEN_MAPPING
#     ]
#     for pool_state in filtered_pool_states:
#         token_a = pool_state["token0"]
#         token_b = pool_state["token1"]
#         logging.getLogger().info(
#             f"Fetching data for token pair: {token_a} and {token_b}"
#         )
#         try:
#             order_book = EkuboOrderBook(token_a, token_b)
#             order_book.fetch_price_and_liquidity()
#             serialized_data = order_book.serialize()
#             connector.write_to_db(OrderBookModel(**serialized_data.model_dump()))
#         except Exception as exc:
#             logger.info(
#                 f"With token pair: {token_a} and {token_b} something happened: {exc}"
#             )
#             continue
#
#
# @app.task(name="haiko_order_book")
# def haiko_order_book():
#     """
#     Fetch the current price and liquidity of the pair from the Haiko API.
#     """
#     all_tokens = set(TOKEN_MAPPING.keys())
#     for base_token in TOKEN_MAPPING:
#         current_tokens = all_tokens - {base_token}
#         for quote_token in current_tokens:
#             try:
#                 order_book = HaikoOrderBook(base_token, quote_token)
#                 order_book.fetch_price_and_liquidity()
#                 serialized_data = order_book.serialize()
#                 connector.write_to_db(OrderBookModel(**serialized_data.model_dump()))
#             except Exception as e:
#                 logger.info(f"With token pair: {base_token} and {quote_token} something happened: {e}")
