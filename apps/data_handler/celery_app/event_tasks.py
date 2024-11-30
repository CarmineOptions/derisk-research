"""
Tasks for processing and storing ZkLend protocol events.
"""

import logging
from datetime import datetime

from data_handler.celery_app.celery_conf import app
from data_handler.handlers.events.nostra.transform_events import NostraTransformer
from data_handler.handlers.events.zklend.transform_events import ZklendTransformer

logger = logging.getLogger(__name__)


@app.task(name="process_zklend_events")
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


@app.task(name="process_nostra_events")
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
