"""
Tests for the protocol_stats module.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard_app.helpers.protocol_stats import (
    get_general_stats,
    get_supply_stats,
    get_collateral_stats,
    get_debt_stats,
    get_utilization_stats,
)
from shared.state import State


@pytest.fixture
def token_addresses():
    """
    Returns a dictionary of token addresses.
    """
    return {
        "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "WBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        "wBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
        "wstETH": "0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",
        "LORDS": "0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",
        "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"
    }


@pytest.fixture
def mock_loan_stats():
    """
    Returns a dictionary of loan stats.
    """
    return {
        "zkLend": pd.DataFrame({
            "Debt (USD)": [1000],
            "Risk-adjusted collateral (USD)": [2000],
            "Collateral (USD)": [2500],
        })
    }


@pytest.fixture
def mock_state(token_addresses):
    """
    Returns a mock state object.
    """
    state = MagicMock(spec=State)
    state.get_protocol_name.return_value = "zkLend"
    state.PROTOCOL_NAME = "zkLend"
    state.compute_number_of_active_loan_entities.return_value = 10
    state.compute_number_of_active_loan_entities_with_debt.return_value = 5
  
    # Setup loan entity with default values
    loan_entity = MagicMock()
    loan_entity.collateral.values = {addr: "0" for addr in token_addresses.values()}
    loan_entity.debt = {addr: "0" for addr in token_addresses.values()}
    loan_entity.collateral.values[token_addresses["ETH"]] = "1000000000000000000"
    loan_entity.debt[token_addresses["ETH"]] = "2000000000000000000"
    state.loan_entities = {"user1": loan_entity}
 
    # Setup token parameters
    class TokenParam:
        """
        A class to represent token parameters.
        """
        def __init__(self, address, symbol):
            self.address = address
            self.underlying_symbol = symbol
            self.underlying_address = address
            self.decimal_factor = 1e18

    token_params = {
        symbol: TokenParam(addr, symbol) 
        for symbol, addr in token_addresses.items()
    }

    state.token_parameters = MagicMock()
    state.token_parameters.collateral = token_params
    state.token_parameters.debt = token_params.copy()

    # Setup interest rate models
    interest_rates = {addr: "1.0" for addr in token_addresses.values()}
    state.interest_rate_models = MagicMock()
    state.interest_rate_models.collateral = interest_rates
    state.interest_rate_models.debt = interest_rates.copy()

    with patch(
        "dashboard_app.helpers.protocol_stats.get_protocol",
        return_value="zkLend"
    ):
        yield state


@pytest.fixture
def mock_prices(token_addresses):
    """
    Returns a dictionary of prices.
    """
    return {
        token_addresses["ETH"]: "2000",
        token_addresses["WBTC"]: "30000",
        token_addresses["USDC"]: "1",
        token_addresses["DAI"]: "1",
        token_addresses["USDT"]: "1",
        token_addresses["wstETH"]: "2100",
        token_addresses["LORDS"]: "0.5",
        token_addresses["STRK"]: "1.2",
    }


@pytest.fixture
def mock_token_settings(token_addresses):
    """
    Returns a dictionary of token settings.
    """
    return {
        symbol: MagicMock(
            decimal_factor=Decimal("1e18"),
            address=addr
        ) for symbol, addr in token_addresses.items()
    }


@pytest.fixture(autouse=True)
def patch_token_settings(mock_token_settings):
    """
    Patches the TOKEN_SETTINGS dictionary.
    """
    with patch(
        "dashboard_app.helpers.protocol_stats.TOKEN_SETTINGS",
        mock_token_settings
    ):
        yield


def test_get_general_stats(mock_state, mock_loan_stats):
    """
    Tests the get_general_stats function.
    """
    result = get_general_stats([mock_state], mock_loan_stats)
 
    assert isinstance(result, pd.DataFrame)
    assert "Protocol" in result.columns
    assert result["Number of active users"].iloc[0] == 10
    assert result["Number of active borrowers"].iloc[0] == 5
    assert result["Total debt (USD)"].iloc[0] == 1000


def test_get_general_stats_empty_state():
    """
    Tests the get_general_stats function with an empty state.
    """
    result = get_general_stats([], {})
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_get_general_stats_invalid_loan_stats(mock_state):
    """
    Tests the get_general_stats function with an invalid loan stats.
    """
    with pytest.raises(KeyError):
        get_general_stats([mock_state], {"InvalidProtocol": pd.DataFrame()})


@patch("dashboard_app.helpers.protocol_stats.get_protocol")
@patch("dashboard_app.helpers.protocol_stats.get_supply_function_call_parameters")
@patch("dashboard_app.helpers.protocol_stats.asyncio.run")
def test_get_supply_stats(
    mock_run, 
    mock_get_params, 
    mock_get_protocol, 
    mock_state, 
    mock_prices, 
    token_addresses,
    mock_token_settings
):
    """
    Tests the get_supply_stats function.
    """
    mock_get_protocol.return_value = "zkLend"
    mock_get_params.return_value = ([token_addresses["ETH"]], "felt_total_supply")
    mock_run.return_value = [Decimal("1000000000000000000")]

    # Convert prices to Decimal
    prices = {k: Decimal(v) for k, v in mock_prices.items()}

    result = get_supply_stats([mock_state], prices)

    assert isinstance(result, pd.DataFrame)
    assert "Protocol" in result.columns
    assert "ETH supply" in result.columns


@patch("dashboard_app.helpers.protocol_stats.get_protocol")
@patch("dashboard_app.helpers.protocol_stats.get_supply_function_call_parameters")
@patch("dashboard_app.helpers.protocol_stats.asyncio.run")
def test_get_supply_stats_blockchain_error(
    mock_run,
    mock_get_params,
    mock_get_protocol,
    mock_state,
    mock_prices,
    token_addresses
):
    """
    Tests the get_supply_stats function with a blockchain error.
    """
    mock_get_protocol.return_value = "zkLend"
    mock_get_params.return_value = ([token_addresses["ETH"]], "felt_total_supply")
    mock_run.side_effect = Exception("Blockchain call failed")

    with pytest.raises(Exception):
        get_supply_stats([mock_state], mock_prices)


@patch("dashboard_app.helpers.protocol_stats.get_protocol")
def test_get_collateral_stats(mock_get_protocol, mock_state, token_addresses):
    """
    Tests the get_collateral_stats function.
    """
    mock_get_protocol.return_value = "zkLend"

    result = get_collateral_stats([mock_state])

    assert isinstance(result, pd.DataFrame)
    assert "Protocol" in result.columns
    assert "ETH collateral" in result.columns


def test_get_collateral_stats_invalid_protocol(mock_state):
    """
    Tests the get_collateral_stats function with an invalid protocol.
    """
    with patch(
        "dashboard_app.helpers.protocol_stats.get_protocol"
    ) as mock_get_protocol:
        mock_get_protocol.return_value = "InvalidProtocol"
        with pytest.raises(ValueError):
            get_collateral_stats([mock_state])


@patch("dashboard_app.helpers.protocol_stats.get_protocol")
def test_get_debt_stats(mock_get_protocol, mock_state, token_addresses):
    """
    Tests the get_debt_stats function.
    """
    mock_get_protocol.return_value = "zkLend"

    result = get_debt_stats([mock_state])

    assert isinstance(result, pd.DataFrame)
    assert "Protocol" in result.columns
    assert "ETH debt" in result.columns


def test_get_debt_stats_invalid_protocol(mock_state):
    """
    Tests the get_debt_stats function with an invalid protocol.
    """
    with patch(
        "dashboard_app.helpers.protocol_stats.get_protocol"
    ) as mock_get_protocol:
        mock_get_protocol.return_value = "InvalidProtocol"
        with pytest.raises(ValueError):
            get_debt_stats([mock_state])


def test_get_utilization_stats():
    """
    Tests the get_utilization_stats function.
    """
    general_stats = pd.DataFrame({
        "Protocol": ["zkLend"],
        "Total debt (USD)": [1000],
    })

    supply_stats = pd.DataFrame({
        "Protocol": ["zkLend"],
        "Total supply (USD)": [4000],
        **{f"{token} supply": [
            1000 if token in ["USDC", "DAI", "USDT", "LORDS", "STRK"] else 1
        ] for token in [
            "ETH", "WBTC", "USDC", "DAI", "USDT", "wstETH", "LORDS", "STRK"
        ]}
    })

    debt_stats = pd.DataFrame({
        "Protocol": ["zkLend"],
        **{f"{token} debt": [
            500 if token in ["USDC", "DAI", "USDT", "LORDS", "STRK"] else 0.5
        ] for token in [
            "ETH", "WBTC", "USDC", "DAI", "USDT", "wstETH", "LORDS", "STRK"
        ]}
    })

    result = get_utilization_stats(general_stats, supply_stats, debt_stats)
 
    utilization_columns = [col for col in result.columns if col != "Protocol"]
    result[utilization_columns] = result[utilization_columns].applymap(
        lambda x: round(x, 4)
    )

    assert isinstance(result, pd.DataFrame)
    assert "Protocol" in result.columns
    assert "Total utilization" in result.columns
    assert "ETH utilization" in result.columns


def test_get_utilization_stats_division_by_zero():
    """
    Tests the get_utilization_stats function with a division by zero.
    """
    general_stats = pd.DataFrame({
        "Protocol": ["zkLend"],
        "Total debt (USD)": [1000],
    })

    supply_stats = pd.DataFrame({
        "Protocol": ["zkLend"],
        "Total supply (USD)": [0], 
        **{f"{token} supply": [0] for token in [
            "ETH", "WBTC", "USDC", "DAI", "USDT", "wstETH", "LORDS", "STRK"
        ]}
    })

    debt_stats = pd.DataFrame({
        "Protocol": ["zkLend"],
        **{f"{token} debt": [0] for token in [
            "ETH", "WBTC", "USDC", "DAI", "USDT", "wstETH", "LORDS", "STRK"
        ]}
    })

    result = get_utilization_stats(general_stats, supply_stats, debt_stats)

    # Check if division by zero results in NaN or infinity
    assert result["Total utilization"].iloc[0] == 1 
    assert result["ETH utilization"].iloc[0] == 0.0
