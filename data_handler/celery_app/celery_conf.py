import os

from celery import Celery
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

# Redis credentials
REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)


ORDER_BOOK_TIME_INTERVAL = int(os.environ.get("ORDER_BOOK_TIME_INTERVAL", 5))


app = Celery(
    main="DataHandler",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

CRONTAB_TIME = os.environ.get("CRONTAB_TIME", "5")

app.conf.beat_schedule = {
    # f'run_loan_states_computation_for_hashtack_v0_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_loan_states_computation_for_hashtack_v0',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    # },
    # f'run_loan_states_computation_for_hashtack_v1_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_loan_states_computation_for_hashtack_v1',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
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
    # f'run_liquidable_debt_computation_for_zklend_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_liquidable_debt_computation_for_zklend',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    # },
    # "constant_product_market_makers_order_book": {
    #     "task": "uniswap_v2_order_book",
    #     "schedule": ORDER_BOOK_TIME_INTERVAL,
    # },
    "ekubo_order_book": {
        "task": "ekubo_order_book",
        "schedule": ORDER_BOOK_TIME_INTERVAL,
    },
}

# from celery_app.tasks import (
    # run_loan_states_computation_for_hashtack_v0,
    # run_loan_states_computation_for_hashtack_v1,
    # run_loan_states_computation_for_nostra_alpha,
    # run_loan_states_computation_for_nostra_mainnet,
    # run_loan_states_computation_for_zklend,
#     run_liquidable_debt_computation_for_zklend,
#     uniswap_v2_order_book,
# )


from celery_app.order_books_tasks import (
    ekubo_order_book,
)
app.autodiscover_tasks(["celery_app.tasks"])
