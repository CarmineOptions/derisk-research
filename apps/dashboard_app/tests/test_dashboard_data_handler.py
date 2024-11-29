import pytest
from unittest.mock import MagicMock, patch
from dashboard_app.helpers.load_data import DashboardDataHandler

@pytest.fixture
def mock_data_connector():
    """Fixture to mock the DataConnector."""
    with patch("dashboard_app.helpers.load_data.DataConnector") as MockConnector:
        connector = MockConnector
        # Mocking fetch_data calls with dummy data
        connector.fetch_data.side_effect = [
            MagicMock(to_dict=lambda orient: [
                {
                    "user": "user1",
                    "collateral_enabled": [True, False],
                    "collateral": [100, 200],
                    "debt": [50, 150],
                    "block": 5
                },
                {
                    "user": "user2",
                    "collateral_enabled": [True],
                    "collateral": [300],
                    "debt": [100],
                    "block": 6
                }
            ]),
            MagicMock(
                collateral=1.5,
                debt=2.0
            ),
        ]
        yield connector

@pytest.fixture
def handler(mock_data_connector):
    """Fixture to initialize DashboardDataHandler."""
    with patch("dashboard_app.helpers.load_data.DataConnector", return_value=mock_data_connector):
        handler = DashboardDataHandler()
        yield handler

# Positive Scenario: Test Initialization
def test_init_dashboard_data_handler(handler):
    assert handler.zklend_state is not None
    assert handler.states == [handler.zklend_state]

# Positive Scenario: Test Successful Data Loading
@patch("dashboard_app.helpers.load_data.get_prices")
def test_load_data_success(mock_get_prices, handler):
    mock_get_prices.return_value = {"token1": 10, "token2": 20}
    handler._collect_token_parameters = MagicMock()
    handler._set_underlying_addresses_to_decimals = MagicMock()
    handler._set_prices = MagicMock()
    handler._get_loan_stats = MagicMock(return_value={"loan_data": "test"})
    handler._get_general_stats = MagicMock(return_value={"general_stats": "test"})
    handler._get_supply_stats = MagicMock(return_value={"supply_stats": "test"})
    handler._get_collateral_stats = MagicMock(return_value={"collateral_stats": "test"})
    handler._get_debt_stats = MagicMock(return_value={"debt_stats": "test"})
    handler._get_utilization_stats = MagicMock(return_value={"utilization_stats": "test"})

    result = handler.load_data()
    assert len(result) == 6
    handler._collect_token_parameters.assert_called_once()
    handler._set_underlying_addresses_to_decimals.assert_called_once()
    handler._set_prices.assert_called_once()

# Negative Scenario: Missing or Invalid Data
def test_load_data_missing_data(handler):
    """Test for handling missing data in load_data method."""
    handler._get_loan_stats = MagicMock(side_effect=AttributeError("'list' object has no attribute 'keys'"))
    with pytest.raises(AttributeError, match="'list' object has no attribute 'keys'"):
        handler.load_data()

# Negative Scenario: Invalid Prices
@patch("dashboard_app.helpers.load_data.get_prices")
def test_load_data_invalid_prices(mock_get_prices, handler):
    mock_get_prices.side_effect = Exception("Price fetch error")
    with pytest.raises(Exception, match="Price fetch error"):
        handler._set_prices()
