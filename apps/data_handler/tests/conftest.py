"""
This module contains the fixtures for the tests.
"""

from unittest.mock import MagicMock

import pytest
from data_handler.db.crud import (
    DBConnector,
    InitializerDBConnector,
    ZkLendEventDBConnector
)
from data_handler.handler_tools.api_connector import DeRiskAPIConnector
from data_handler.handler_tools.data_parser.zklend import ZklendDataParser


@pytest.fixture(scope="module")
def mock_db_connector() -> None:
    """
    Mock DBConnector
    :return: None.
    """
    mock_connector = MagicMock(spec=DBConnector)
    mock_connector.get_last_block.return_value = 12345
    yield mock_connector


@pytest.fixture(scope="module")
def mock_initializer_db_connector() -> None:
    """
    Mock for InitializerDBConnector
    :return: None
    """
    mock_initializer_connector = MagicMock(spec=InitializerDBConnector)
    mock_initializer_connector.engine = MagicMock()
    mock_initializer_connector.connection = MagicMock()
    yield mock_initializer_connector


@pytest.fixture(scope="function")
def mock_api_connector():
    """
    Creates a mock API connector for testing.
    """
    mock_api_connector = MagicMock(spec=DeRiskAPIConnector)
    yield mock_api_connector


@pytest.fixture(scope="function")
def mock_zklend_event_db_connector():
    """
    Mock for ZkLendEventDBConnector
    :return: None
    """
    mock_zklend_event_db_connector = MagicMock(spec=ZkLendEventDBConnector)
    yield mock_zklend_event_db_connector


@pytest.fixture(scope="function")
def mock_zklend_data_parser():
    """
    Mock for ZklendDataParser
    :return: None
    """
    mock_zklend_data_parser = MagicMock(spec=ZklendDataParser)
    yield mock_zklend_data_parser
