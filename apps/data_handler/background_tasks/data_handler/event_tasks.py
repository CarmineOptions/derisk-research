"""
Tasks for processing and storing ZkLend protocol events.
"""

import logging
import asyncio
from datetime import datetime
import threading

from celery import shared_task
from data_handler.handlers.events.nostra.transform_events import NostraTransformer
from data_handler.handlers.events.zklend.transform_events import ZklendTransformer
from data_handler.handlers.loan_states.vesu.events import VesuLoanEntity

logger = logging.getLogger(__name__)

CHUNK_SIZE = 5

"""in the event of mulitple loop run async method in a new thread to avoid event loop conflicts"""
def run_async_in_thread(coro):
    """Run an async coroutine in a new thread with its own event loop."""
    result = None
    exception = None

    def run_coro():
        nonlocal result, exception
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        except Exception as e:
            exception = e
        finally:
            loop.close()

    thread = threading.Thread(target=run_coro)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result


@shared_task(name="process_zklend_events")
def process_zklend_events():
    """
    Process and store ZkLend protocol events.
    Fetches events from the blockchain, transforms them into the required format,
    and saves them to the database.
    """
    start_time = datetime.utcnow()
    logger.info("Starting ZkLend event processing")
    try:
        # Initialize and run transformer
        transformer = ZklendTransformer()
        transformer.run()
        # Log success metrics
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "Successfully processed ZkLend events in %.2fs. Blocks: %d to %d",
            execution_time,
            transformer.last_block - transformer.PAGINATION_SIZE,
            transformer.last_block,
        )
    except (
        ValueError,
        TypeError,
        RuntimeError,
    ) as exc:  # Catching more specific exceptions
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Error processing ZkLend events after %.2fs: %s",
            execution_time,
            exc,
            exc_info=True,
        )
    except Exception as exc:  # Still keeping a general exception catch as a fallback
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Unexpected error processing ZkLend events after %.2fs: %s",
            execution_time,
            exc,
            exc_info=True,
        )


@shared_task(name="process_nostra_events")
def process_nostra_events():
    """
    Process and store Nostra protocol events.
    Fetches events from the blockchain, transforms them into the required format,
    and saves them to the database.
    """
    start_time = datetime.utcnow()
    logger.info("Starting Nostra event processing")
    try:
        # Initialize and run transformer
        transformer = NostraTransformer()
        transformer.run()
        # Log success metrics
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "Successfully processed Nostra events in %.2fs. Blocks: %d to %d",
            execution_time,
            transformer.last_block - transformer.PAGINATION_SIZE,
            transformer.last_block,
        )
    except (
        ValueError,
        TypeError,
        RuntimeError,
    ) as exc:  # Catching more specific exceptions
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Error processing Nostra events after %.2fs: %s",
            execution_time,
            exc,
            exc_info=True,
        )
    except Exception as exc:  # Still keeping a general exception catch as a fallback
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Unexpected error processing Nostra events after %.2fs: %s",
            execution_time,
            exc,
            exc_info=True,
        )


@shared_task(name="process_vesu_events", bind=True, max_retries=3)
def process_vesu_events(self):
    """
    Process and store Vesu protocol events.
    Fetches ModifyPosition events from the blockchain, updates user positions,
    and stores them in a mock database.
    """
    start_time = datetime.utcnow()
    logger.info("Starting Vesu event processing")
    try:
        vesu_entity = VesuLoanEntity()
        run_async_in_thread(vesu_entity.update_positions_data())
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "Successfully processed Vesu events in %.2fs (UTC). Blocks: %d to %d",
            execution_time, 
            vesu_entity.last_processed_block - CHUNK_SIZE, # default as update_positions_data chunk_size
            vesu_entity.last_processed_block,
        )
    except (ValueError, TypeError, RuntimeError) as exc:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Error processing Vesu events after %.2fs: %s",
            execution_time,
            exc,
            exc_info=True,
        )
        self.retry(countdown=60)
    except Exception as exc:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            "Unexpected error processing Vesu events after %.2fs: %s",
            execution_time,
            exc,
            exc_info=True,
        )
        self.retry(countdown=60)


