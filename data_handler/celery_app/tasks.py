from celery import shared_task
import logging
from time import monotonic
from data_handler.handlers.loan_states.hashtack_v0.run import HashtackV0StateComputation
from data_handler.handlers.loan_states.hashtack_v1.run import HashtackV1StateComputation
from data_handler.handlers.loan_states.zklend.run import ZkLendLoanStateComputation
from data_handler.handlers.loan_states.nostra_alpha.run import NostraAlphaStateComputation
from data_handler.handlers.loan_states.nostra_mainnet.run import NostraMainnetStateComputation


@shared_task
def run_loan_states_computation_for_hashtack_v0():
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting Hashtack V0 loan state computation")
    computation = HashtackV0StateComputation()
    computation.run()

    logging.info(
        "Finished Hashtack V0 loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


@shared_task
def run_loan_states_computation_for_hashtack_v1():
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting Hashtack V1 loan state computation")
    computation = HashtackV1StateComputation()
    computation.run()

    logging.info(
        "Finished Hashtack V1 loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


@shared_task
def run_loan_states_computation_for_zklend():
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting zkLend loan state computation")
    computation = ZkLendLoanStateComputation()
    computation.run()

    logging.info(
        "Finished zkLend loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


@shared_task
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


@shared_task
def run_loan_states_computation_for_nostra_mainnet():
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logging.info("Starting Nostra Mainnet loan state computation")
    computation = NostraMainnetStateComputation()
    computation.run()

    logging.info(
        "Finished Nostra Mainnet loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )



