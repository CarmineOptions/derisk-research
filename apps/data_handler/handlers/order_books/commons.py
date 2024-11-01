"""
Module for configuring and retrieving a logger with file and optional console output.
Enables detailed logging with timestamped log files for order book processing.
"""
import logging
from datetime import datetime
from pathlib import Path


def get_logger(name: str, path: str | Path, echo: bool = False):
    """
    Configure and get logger for haiko order book
    :param name: name of the logger
    :param path: path to log file
    :param echo: write logs in terminal if set to True
    :return: Configured logger
    """
    path_dir = Path(path)
    path_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    log_path = path_dir / datetime.now().strftime("order_book_%Y%m%d_%H%M%S.log")
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if not echo:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
