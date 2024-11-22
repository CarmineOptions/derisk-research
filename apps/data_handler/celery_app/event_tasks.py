"""
Tasks for processing and storing ZkLend protocol events.
"""

import logging
from datetime import datetime

from data_handler.celery_app.celery_conf import app
from data_handler.handlers.events.zklend import ZklendTransformer

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
            f"Successfully processed ZkLend events in {execution_time:.2f}s. "
            f"Blocks: {transformer.last_block - transformer.PAGINATION_SIZE} "
            f"to {transformer.last_block}"
        )
        
    except Exception as exc:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"Error processing ZkLend events after {execution_time:.2f}s: {exc}",
            exc_info=True
        )
        raise


if __name__ == "__main__":
    process_zklend_events()