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