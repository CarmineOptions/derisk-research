"""
This module contains the fixtures for the tests.
"""

from unittest.mock import MagicMock, patch

import pytest
from data_handler.db.crud import (
    DBConnector,
    InitializerDBConnector,
    NostraEventDBConnector,
    ZkLendEventDBConnector,
)
from data_handler.handler_tools.api_connector import DeRiskAPIConnector
from data_handler.handler_tools.data_parser.nostra import NostraDataParser
from data_handler.handler_tools.data_parser.zklend import ZklendDataParser
from data_handler.handlers.events.nostra.transform_events import NostraTransformer


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


@pytest.fixture(scope="function")
def mock_nostra_event_db_connector():
    """
    Mock for NostraEventDBConnector
    :return: None
    """
    mock_nostra_event_db_connector = MagicMock(spec=NostraEventDBConnector)
    mock_nostra_event_db_connector.get_last_block.return_value = 0
    mock_nostra_event_db_connector.create_bearing_collateral_burn_event = MagicMock()
    mock_nostra_event_db_connector.create_bearing_collateral_mint_event = MagicMock()
    mock_nostra_event_db_connector.create_debt_burn_event = MagicMock()
    mock_nostra_event_db_connector.create_debt_mint_event = MagicMock()
    mock_nostra_event_db_connector.create_debt_transfer_event = MagicMock()
    mock_nostra_event_db_connector.create_interest_rate_model_event = MagicMock()
    mock_nostra_event_db_connector.create_non_interest_bearing_collateral_burn_event = (
        MagicMock()
    )
    mock_nostra_event_db_connector.create_non_interest_bearing_collateral_mint_event = (
        MagicMock()
    )
    yield mock_nostra_event_db_connector


@pytest.fixture(scope="function")
def transformer(
    mock_api_connector,
    mock_nostra_event_db_connector,
):
    """
    Creates an instance of NostraTransformer with mocked dependencies.
    """
    with patch(
        "data_handler.handlers.events.nostra.transform_events.NostraEventDBConnector",
        return_value=mock_nostra_event_db_connector,
    ), patch(
        "data_handler.handlers.events.nostra.transform_events.DeRiskAPIConnector",
        return_value=mock_api_connector,
    ):
        transformer = NostraTransformer()
        transformer.api_connector = mock_api_connector
        transformer.db_connector = mock_nostra_event_db_connector
        transformer.data_parser = NostraDataParser()
        return transformer
