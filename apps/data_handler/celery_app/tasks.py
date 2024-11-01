"""Celery tasks for running loan state and liquidable debt computations, 
and fetching Uniswap V2 order book data."""

import logging
from time import monotonic

# from data_handler.handlers.loan_states.nostra_mainnet.run import NostraMainnetStateComputation
from data_handler.handlers.liquidable_debt.protocols import (
    hashstack_v0,
    hashstack_v1,
    nostra_alpha,
    nostra_mainnet,
    zklend,
)

# from data_handler.handlers.loan_states.hashtack_v0.run import HashtackV0StateComputation
# from data_handler.handlers.loan_states.hashtack_v1.run import HashtackV1StateComputation
# from data_handler.handlers.loan_states.zklend.run import ZkLendLoanStateComputation
from data_handler.handlers.loan_states.nostra_alpha.run import (
    NostraAlphaStateComputation,
)
from data_handler.handlers.order_books.constants import TOKEN_MAPPING
from data_handler.handlers.order_books.ekubo.api_connector import EkuboAPIConnector
from data_handler.handlers.order_books.uniswap_v2.main import UniswapV2OrderBook

from data_handler.db.crud import DBConnector
from data_handler.db.models import OrderBookModel

from data_handler.celery_app.celery_conf import app

connector = DBConnector()

# @app.task(name="run_loan_states_computation_for_hashtack_v0")
# def run_loan_states_computation_for_hashtack_v0():
#     start = monotonic()
#     logging.basicConfig(level=logging.INFO)
#
#     logging.info("Starting Hashtack V0 loan state computation")
#     computation = HashtackV0StateComputation()
#     computation.run()
#
#     logging.info(
#         "Finished Hashtack V0 loan state computation, Time taken: %s seconds",
#         monotonic() - start,
#     )

# @app.task(name="run_loan_states_computation_for_hashtack_v1")
# def run_loan_states_computation_for_hashtack_v1():
#     start = monotonic()
#     logging.basicConfig(level=logging.INFO)
#
#     logging.info("Starting Hashtack V1 loan state computation")
#     computation = HashtackV1StateComputation()
#     computation.run()
#
#     logging.info(
#         "Finished Hashtack V1 loan state computation, Time taken: %s seconds",
#         monotonic() - start,
#     )

# @app.task(name="run_loan_states_computation_for_zklend")
# def run_loan_states_computation_for_zklend():
#     start = monotonic()
#     logging.basicConfig(level=logging.INFO)
#
#     logging.info("Starting zkLend loan state computation")
#     computation = ZkLendLoanStateComputation()
#     computation.run()
#
#     logging.info(
#         "Finished zkLend loan state computation, Time taken: %s seconds",
#         monotonic() - start,
#     )


@app.task(name="run_loan_states_computation_for_nostra_alpha")
def run_loan_states_computation_for_nostra_alpha():
    """fn docstring"""
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting Nostra Alpha loan state computation")
    computation = NostraAlphaStateComputation()
    computation.run()

    logging.info(
        "Finished Nostra Alpha loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


# @app.task(name="run_loan_states_computation_for_nostra_mainnet")
# def run_loan_states_computation_for_nostra_mainnet():
#     start = monotonic()
#     logging.basicConfig(level=logging.INFO)
#
#     logging.info("Starting Nostra Mainnet loan state computation")
#     computation = NostraMainnetStateComputation()
#     computation.run()
#
#     logging.info(
#         "Finished Nostra Mainnet loan state computation, Time taken: %s seconds",
#         monotonic() - start,
#     )
#


@app.task(name="uniswap_v2_order_book")
def uniswap_v2_order_book():
    """
    Fetch the current price and liquidity of the pair from the Uniswap V2 AMMs.
    """
    all_tokens = set(TOKEN_MAPPING.keys())
    for base_token in TOKEN_MAPPING:
        current_tokens = all_tokens - {base_token}
        for quote_token in current_tokens:
            try:
                order_book = UniswapV2OrderBook(base_token, quote_token)
                order_book.fetch_price_and_liquidity()
                serialized_data = order_book.serialize()
                connector.write_to_db(OrderBookModel(**serialized_data.model_dump()))
            except Exception as e:
                logging.info(
                    f"With token pair: {base_token} and {quote_token} something happened: {e}"
                )


@app.task(name="run_liquidable_debt_computation_for_zklend")
def run_liquidable_debt_computation_for_zklend():
    """fn docstring"""
    logging.info("Starting zkLend liquidable debt computation")
    zklend.run()
    logging.info("zkLend liquidable debt computation finished")


@app.task(name="run_liquidable_debt_computation_for_nostra_alpha")
def run_liquidable_debt_computation_for_nostra_alpha():
    """fn docstring"""
    logging.info("Starting nostra alpha liquidable debt computation")
    nostra_alpha.run()
    logging.info("Nostra alpha liquidable debt computation finished")


@app.task(name="run_liquidable_debt_computation_for_hashstack_v0")
def run_liquidable_debt_computation_for_hashstack_v0():
    """fn docstring"""
    logging.info("Starting hashstack v0 liquidable debt computation")
    hashstack_v0.run()
    logging.info("Hashstack v0 liquidable debt computation finished")


@app.task(name="run_liquidable_debt_computation_for_nostra_mainnet")
def run_liquidable_debt_computation_for_nostra_mainnet():
    """fn docstring"""
    logging.info("Starting nostra mainnet liquidable debt computation")
    nostra_mainnet.run()
    logging.info("Nostra mainnet liquidable debt computation finished")


@app.task(name="run_liquidable_debt_computation_for_hashstack_v1")
def run_liquidable_debt_computation_for_hashstack_v1():
    """fn docstring"""
    logging.info("Starting hashstack v1 liquidable debt computation")
    hashstack_v1.run()
    logging.info("Hashstack v1 liquidable debt computation finished")
