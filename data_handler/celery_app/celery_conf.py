import os

from celery import Celery
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

# Redis credentials
REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)


app = Celery(
    main="DataHandler",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

CRONTAB_TIME = os.environ.get("CRONTAB_TIME", "1")

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
    f'run_loan_states_computation_for_nostra_alpha_every_{CRONTAB_TIME}_mins': {
        'task': 'run_loan_states_computation_for_nostra_alpha',
        'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    },
    # f'run_loan_states_computation_for_nostra_mainnet_every_{CRONTAB_TIME}_mins': {
    #     'task': 'run_loan_states_computation_for_nostra_mainnet',
    #     'schedule': crontab(minute=f'*/{CRONTAB_TIME}'),
    # },
}
# from celery_app.tasks import (
    # run_loan_states_computation_for_hashtack_v0,
    # run_loan_states_computation_for_hashtack_v1,
    # run_loan_states_computation_for_nostra_alpha,
    # run_loan_states_computation_for_nostra_mainnet,
    # run_loan_states_computation_for_zklend,
# )

app.autodiscover_tasks(["celery_app.tasks"])



