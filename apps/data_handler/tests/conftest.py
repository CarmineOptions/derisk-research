"""
This module contains the fixtures for the tests.
"""

from unittest.mock import MagicMock

import pytest
from data_handler.db.crud import DBConnector, InitializerDBConnector
from data_handler.handler_tools.api_connector import DeRiskAPIConnector

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
    yield mock_initializer_connector


@pytest.fixture(scope="function")
def mock_api_connector():
    """
    Creates a mock API connector for testing.
    """
    mock_api_connector = MagicMock(spec=DeRiskAPIConnector)
    yield mock_api_connector
