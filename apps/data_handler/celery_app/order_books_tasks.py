"""
Order books tasks module for handling Ekubo and Haiko order book operations.
Provides Celery tasks for fetching and processing order book data from different DEXes.
"""

import logging
from data_handler.celery_app.celery_conf import app
from data_handler.db.crud import DBConnector
from data_handler.db.models import OrderBookModel
from data_handler.handlers.order_books.constants import TOKEN_MAPPING
from data_handler.handlers.order_books.ekubo.api_connector import EkuboAPIConnector
from data_handler.handlers.order_books.ekubo.main import EkuboOrderBook
from data_handler.handlers.order_books.haiko.main import HaikoOrderBook

logger = logging.getLogger(__name__)
connector = DBConnector()

@app.task(name="ekubo_order_book")
def ekubo_order_book():
    """
    Fetch the current price and liquidity of token pairs from the Ekubo API.
    
    This task:
    1. Fetches all pool states from Ekubo
    2. Filters pools for supported token pairs
    3. Processes each pool to get price and liquidity data
    4. Stores the data in the database
    
    Raises:
        Exception: Logs any errors during processing of individual token pairs
    """
    pool_states = EkuboAPIConnector().get_pools()
    filtered_pool_states = [
        pool_state
        for pool_state in pool_states
        if isinstance(pool_state, dict)
        and pool_state["token0"] in TOKEN_MAPPING
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

@app.task(name="haiko_order_book")
def haiko_order_book():
    """
    Fetch the current price and liquidity of token pairs from the Haiko API.
    
    This task:
    1. Iterates through all possible token pair combinations
    2. For each pair, fetches price and liquidity data
    3. Stores the data in the database
    
    Raises:
        Exception: Logs any errors during processing of individual token pairs
    """
    all_tokens = set(TOKEN_MAPPING.keys())
    
    for base_token in TOKEN_MAPPING:
        current_tokens = all_tokens - {base_token}
        for quote_token in current_tokens:
            try:
                order_book = HaikoOrderBook(base_token, quote_token)
                order_book.fetch_price_and_liquidity()
                serialized_data = order_book.serialize()
                connector.write_to_db(OrderBookModel(**serialized_data.model_dump()))
            except Exception as e:
                logger.info(
                    f"With token pair: {base_token} and {quote_token} something happened: {e}"
                )

if __name__ == "__main__":
    ekubo_order_book()