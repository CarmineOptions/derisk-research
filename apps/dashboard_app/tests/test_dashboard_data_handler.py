from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pandas import DataFrame

pytest.importorskip("data_handler")
from helpers.load_data import DashboardDataHandler


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
    with patch("dashboard_app.helpers.load_data.DataConnectorAsync") as MockConnector:
        connector = MockConnector

        connector.fetch_protocol_first_block_number.return_value = 1
        connector.fetch_protocol_last_block_number.return_value = 6

        # Mocking fetch_data calls with dummy data
        def fetch_data_side_effect(query, **kwargs):
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
        state.PROTOCOL_NAME = "zkLend"
        state.get_protocol_name = "zkLend"
        yield state


@pytest.fixture
def mock_get_prices():
    """Fixture to mock the get_prices function."""
    with patch("dashboard_app.helpers.load_data.get_prices") as MockGetPrices:
        MockGetPrices.return_value = {"token1": 10, "token2": 20}
        yield MockGetPrices


@pytest.fixture
async def handler(mock_data_connector, mock_zklend_state, mock_get_prices):
    """Fixture to initialize DashboardDataHandler."""
    with patch(
        "dashboard_app.helpers.load_data.DataConnectorAsync",
        return_value=mock_data_connector,
    ):
        handler = await DashboardDataHandler.create()
        yield handler


@pytest.mark.asyncio
async def test_init_dashboard_data_handler(handler):
    """Test to ensure all attributes were set during DashboardDataHandler init."""
    assert handler.zklend_state is not None
    assert handler.zklend_state.get_protocol_name == "zkLend"
    assert handler.zklend_state.last_block_number is not None
    assert (
        handler.zklend_state.last_block_number
        == await handler.data_connector.fetch_protocol_last_block_number("zkLend")
    )
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


@patch("dashboard_app.helpers.load_data.ZkLendState")
@patch("dashboard_app.helpers.load_data.DataConnectorAsync")
@pytest.mark.asyncio
async def test_init_dashboard_went_sideways(mock_data_connector, mock_zklend_state):
    """Test to ensure the DashboardDataHandler init handles exceptions."""
    mock_data_connector.side_effect = Exception("DataConnector failed")
    with pytest.raises(Exception, match="DataConnector failed"):
        handler = await DashboardDataHandler.create()
    mock_data_connector.side_effect = None
    mock_zklend_state.side_effect = Exception("ZkLendState failed")
    with pytest.raises(Exception, match="ZkLendState failed"):
        handler = await DashboardDataHandler.create()


def test_set_prices(handler):
    """Test for setting prices in set_prices method."""
    handler._set_prices()
    assert handler.prices == {"token1": 10, "token2": 20}


@patch("dashboard_app.helpers.protocol_stats.add_leading_zeros", return_value="token1")
@patch("dashboard_app.helpers.load_data.get_loans_table_data")
def test_load_data_success(
    mock_get_loans_table_data, mock_add_leading_zeros, handler, capfd
):
    """Test for successful data loading in load_data method."""
    mock_get_loans_table_data.return_value = DataFrame(
        [
            {
                "User": "user1",
                "Protocol": "zkLend",
                "Collateral (USD)": 1000,
                "Risk-adjusted collateral (USD)": 900,
                "Debt (USD)": 500,
                "Health factor": 2.0,
                "Standardized health factor": 1.8,
                "Collateral": "100 ETH",
                "Debt": "50 DAI",
            },
            {
                "User": "user2",
                "Protocol": "zkLend",
                "Collateral (USD)": 2000,
                "Risk-adjusted collateral (USD)": 1800,
                "Debt (USD)": 1000,
                "Health factor": 2.0,
                "Standardized health factor": 1.8,
                "Collateral": "200 ETH",
                "Debt": "100 DAI",
            },
        ]
    )
    handler._collect_token_parameters = MagicMock()
    handler._set_underlying_addresses_to_decimals = MagicMock()

    handler._get_collateral_stats = MagicMock(
        return_value=DataFrame([{"collateral_stats": "test"}])
    )
    handler._get_debt_stats = MagicMock(
        return_value=DataFrame([{"debt_stats": "test"}])
    )

    result = handler.load_data()
    assert len(result) == 6
    assert result[0] == handler.zklend_state
    assert result[1].to_dict(orient="records")[0].get("protocol") == "zkLend"
    assert result[2].to_dict(orient="records")[0].get("protocol") == "zkLend"
    assert result[3].to_dict(orient="records")[0].get("collateral_stats") == "test"
    assert result[4].to_dict(orient="records")[0].get("debt_stats") == "test"
    assert result[5].to_dict(orient="records")[0].get("Protocol") == "zkLend"


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
