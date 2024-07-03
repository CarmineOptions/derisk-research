import logging
from time import monotonic

from db.crud import DBConnector
from db.models import OrderBookModel
from handlers.order_books.constants import TOKEN_MAPPING
from .celery_conf import app
from handlers.order_books.ekubo.api_connector import EkuboAPIConnector
# from handlers.loan_states.hashtack_v0.run import HashtackV0StateComputation
# from handlers.loan_states.hashtack_v1.run import HashtackV1StateComputation
# from handlers.loan_states.zklend.run import ZkLendLoanStateComputation
from handlers.loan_states.nostra_alpha.run import NostraAlphaStateComputation
# from handlers.loan_states.nostra_mainnet.run import NostraMainnetStateComputation
from handlers.liquidable_debt.protocols import zklend
from handlers.order_books.uniswap_v2.main import UniswapV2OrderBook

connector = DBConnector()


#@app.task(name="run_loan_states_computation_for_hashtack_v0")
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


#@app.task(name="run_loan_states_computation_for_hashtack_v1")
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
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting Nostra Alpha loan state computation")
    computation = NostraAlphaStateComputation()
    computation.run()

    logging.info(
        "Finished Nostra Alpha loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


#@app.task(name="run_loan_states_computation_for_nostra_mainnet")
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
                logging.info(f"With token pair: {base_token} and {quote_token} something happened: {e}")


@app.task(name="run_liquidable_debt_computation_for_zklend")
def run_liquidable_debt_computation_for_zklend():
    logging.info("Starting zkLend liquidable debt computation")
    zklend.run()
    logging.info("zkLend liquidable debt computation finished")


