"""
Celery configuration for scheduling periodic tasks.
"""

# run_loan_states_computation_for_nostra_mainnet,; run_loan_states_computation_for_zklend,;
# run_liquidable_debt_computation_for_nostra_alpha,;
# run_liquidable_debt_computation_for_nostra_mainnet,;
# uniswap_v2_order_book,

# from data_handler.celery_app.tasks import (
#     run_liquidable_debt_computation_for_zklend, )
# from data_handler.celery_app.order_books_tasks import ekubo_order_book
import os

from celery import Celery
from celery.schedules import crontab
from shared.constants import CRONTAB_TIME
from dotenv import load_dotenv

load_dotenv()

# Redis credentials
REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)

ORDER_BOOK_TIME_INTERVAL = int(os.environ.get("ORDER_BOOK_TIME_INTERVAL", 5))

# Tasks settings
CHECK_DATA_CHANGES_PERIOD = int(
    os.environ.get("CHECK_DATA_CHANGES_PERIOD", 5)  # 60 * 30
)  # in minutes

app = Celery(
    main="DataHandler",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

# TODO reuse

print("#AXCHECK_DATA_CHANGES_PERIOD", CHECK_DATA_CHANGES_PERIOD, CRONTAB_TIME)

app.conf.beat_schedule = {
    # },
    # f'run_loan_states_computation_for_zklend_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_loan_states_computation_for_zklend',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    # },
    # f'run_loan_states_computation_for_nostra_alpha_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_loan_states_computation_for_nostra_alpha',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    # },
    # f'run_loan_states_computation_for_nostra_mainnet_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_loan_states_computation_for_nostra_mainnet',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    # },
    f"run_liquidable_debt_computation_for_zklend_every_{CRONTAB_TIME}_mins": {
        "task": "run_liquidable_debt_computation_for_zklend",
        "schedule": crontab(minute=f"*/{CRONTAB_TIME}"),
    },
    # "constant_product_market_makers_order_book": {
    #     "task": "uniswap_v2_order_book",
    #     "schedule": ORDER_BOOK_TIME_INTERVAL,
    # },
    # f"run_ekubo_order_book_{ORDER_BOOK_TIME_INTERVAL}_mins": {
    #     "task": "ekubo_order_book",
    #     "schedule": ORDER_BOOK_TIME_INTERVAL,
    # },
    f"run_ekubo_order_book_{CRONTAB_TIME}_mins": {
        "task": "ekubo_order_book",
        "schedule": crontab(minute=f"*/{CRONTAB_TIME}"),
    },
    f"process_zklend_events_{CRONTAB_TIME}_mins": {
        "task": "process_zklend_events",
        "schedule": crontab(minute=f"*/{CRONTAB_TIME}"),
    },
    f"process_nostra_events_{CRONTAB_TIME}_mins": {
        "task": "process_nostra_events",
        "schedule": crontab(minute=f"*/{CRONTAB_TIME}"),
    },
    f"process_vesu_events_every_{CRONTAB_TIME}_mins": {
        "task": "process_vesu_events",
        "schedule": crontab(minute=f"*/{CRONTAB_TIME}"),
    },
    # f"check_health_ratio_level_changes_{CHECK_DATA_CHANGES_PERIOD}_mins": {
    #     "task": "check_health_ratio_level_changes",
    #     "schedule": crontab(minute=f"*/{CHECK_DATA_CHANGES_PERIOD}"),
    # },
}

from data_handler.background_tasks.data_handler.order_books_tasks import (
    ekubo_order_book,
)
from data_handler.background_tasks.data_handler.generic_tasks import (
    run_liquidable_debt_computation_for_zklend,
)

# from shared.background_tasks.tasks import check_health_ratio_level_changes

from data_handler.background_tasks.data_handler.event_tasks import process_zklend_events
from data_handler.background_tasks.data_handler.event_tasks import process_nostra_events
from data_handler.background_tasks.data_handler.event_tasks import process_vesu_events


# run_loan_states_computation_for_nostra_alpha,; run_loan_states_computation_for_nostra_mainnet,;
# run_loan_states_computation_for_zklend,; run_liquidable_debt_computation_for_nostra_alpha,;
# run_liquidable_debt_computation_for_nostra_mainnet,;
# uniswap_v2_order_book,

# TODO
# app.autodiscover_tasks(["celery_app.tasks", "celery_app.order_books_tasks"])
