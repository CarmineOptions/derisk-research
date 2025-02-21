from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pandas import DataFrame

from dashboard_app.helpers.load_data import DashboardDataHandler

ZKLEND_DATA = DataFrame(
    [
        {
            "user": "user1",
            "collateral_enabled": [True, False],
            "collateral": [100, 200],
            "debt": [50, 150],
            "block": 5,
        },
        {
            "user": "user2",
            "collateral_enabled": [True],
            "collateral": [300],
            "debt": [100],
            "block": 6,
        },
    ]
)

ZKLEND_INTEREST_RATE = DataFrame({"collateral": [1.5], "debt": [2.0]})


@pytest.fixture
def mock_data_connector():
    """Fixture to mock the DataConnector."""
    with patch("dashboard_app.helpers.load_data.DataConnector") as MockConnector:
        connector = MockConnector

        # Mocking fetch_data calls with dummy data
        def fetch_data_side_effect(query):
            if query == connector.ZKLEND_SQL_QUERY:
                return ZKLEND_DATA
            elif query == connector.ZKLEND_INTEREST_RATE_SQL_QUERY:
                return ZKLEND_INTEREST_RATE
            else:
                raise ValueError(f"Unexpected query: {query}")

        connector.fetch_data.side_effect = fetch_data_side_effect
        yield connector


@pytest.fixture
def mock_zklend_state():
    """Fixture to mock the ZkLendState."""
    with patch("dashboard_app.helpers.load_data.ZkLendState") as MockZkLendState:
        state = MockZkLendState.return_value
        state.load_entities = MagicMock()
        state.collect_token_parameters = AsyncMock()
        yield state


@pytest.fixture
def handler(mock_data_connector, mock_zklend_state):
    """Fixture to initialize DashboardDataHandler."""
    with patch(
        "dashboard_app.helpers.load_data.DataConnector",
        return_value=mock_data_connector,
    ):
        handler = DashboardDataHandler()
        yield handler


def test_init_dashboard_data_handler(handler):
    """Test to ensure all attributes were set during DashboardDataHandler init."""
    assert handler.zklend_state is not None
    assert handler.zklend_state.last_block_number == ZKLEND_DATA["block"].max()
    assert (
        handler.zklend_state.interest_rate_models.collateral
        == ZKLEND_INTEREST_RATE["collateral"].iloc[0]
    )
    assert (
        handler.zklend_state.interest_rate_models.debt
        == ZKLEND_INTEREST_RATE["debt"].iloc[0]
    )
    assert handler.prices is None
    assert handler.states == [handler.zklend_state]


@patch("dashboard_app.helpers.load_data.DataConnector")
@patch("dashboard_app.helpers.load_data.ZkLendState")
def test_init_dashboard_went_sideways(mock_data_connector, mock_zklend_state):
    """Test to ensure the DashboardDataHandler init handles exceptions."""
    mock_data_connector.side_effect = Exception("DataConnector failed")
    with pytest.raises(Exception, match="DataConnector failed"):
        handler = DashboardDataHandler()
    mock_data_connector.side_effect = None
    mock_zklend_state.side_effect = Exception("ZkLendState failed")
    with pytest.raises(Exception, match="ZkLendState failed"):
        handler = DashboardDataHandler()


@patch("dashboard_app.helpers.load_data.get_prices")
def test_load_data_success(mock_get_prices, handler):
    """Test for successful data loading in load_data method."""
    mock_get_prices.return_value = {"token1": 10, "token2": 20}
    handler._collect_token_parameters = MagicMock()
    handler._set_underlying_addresses_to_decimals = MagicMock()
    handler._set_prices = MagicMock()
    handler._get_loan_stats = MagicMock(return_value={"loan_data": "test"})
    handler._get_general_stats = MagicMock(return_value={"general_stats": "test"})
    handler._get_supply_stats = MagicMock(return_value={"supply_stats": "test"})
    handler._get_collateral_stats = MagicMock(return_value={"collateral_stats": "test"})
    handler._get_debt_stats = MagicMock(return_value={"debt_stats": "test"})
    handler._get_utilization_stats = MagicMock(
        return_value={"utilization_stats": "test"}
    )

    result = handler.load_data()
    assert len(result) == 6
    handler._collect_token_parameters.assert_called_once()
    handler._set_underlying_addresses_to_decimals.assert_called_once()
    handler._set_prices.assert_called_once()


def test_load_data_missing_data(handler):
    """Test for handling missing data in load_data method."""
    handler._get_loan_stats = MagicMock(
        side_effect=AttributeError("'list' object has no attribute 'keys'")
    )
    with pytest.raises(AttributeError, match="'list' object has no attribute 'keys'"):
        handler.load_data()
    handler._get_loan_stats = MagicMock(return_value=None)
    with pytest.raises(TypeError, match="'NoneType' object is not subscriptable"):
        handler.load_data()
    handler._get_general_stats = MagicMock(side_effect=KeyError("KeyError: 'zkLend'"))
    with pytest.raises(KeyError, match="KeyError: 'zkLend'"):
        handler.load_data()


@patch("dashboard_app.helpers.load_data.get_prices")
def test_load_data_invalid_prices(mock_get_prices, handler):
    """Test for handling invalid prices in load_data method."""
    mock_get_prices.side_effect = Exception("Price fetch error")
    with pytest.raises(Exception, match="Price fetch error"):
        handler._set_prices()
    mock_get_prices.side_effect = None
    mock_get_prices.return_value = {}
    handler._set_prices()
    assert handler.prices == {}
    with pytest.raises(KeyError):
        handler.load_data()
