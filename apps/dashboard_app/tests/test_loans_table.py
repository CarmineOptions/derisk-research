import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from dashboard_app.helpers.loans_table import (
    get_protocol,
    get_loans_table_data,
    get_supply_function_call_parameters,
)
from shared.state import State
from shared.custom_types import Prices

class MockLoanEntity:
    def __init__(self):
        self.collateral = {"ETH": 1000}
        self.debt = {"ETH": 500}

    def compute_collateral_usd(self, *args, **kwargs):
        return 1000.0

    def compute_debt_usd(self, *args, **kwargs):
        return 500.0

    def compute_health_factor(self, *args, **kwargs):
        return 2.0

    def get_collateral_str(self, *args, **kwargs):
        return "100 ETH"

    def get_debt_str(self, *args, **kwargs):
        return "50 USDC"


class MockState(State):
    def __init__(self, protocol_name):
        self.PROTOCOL_NAME = protocol_name
        self.loan_entities = {"User1": MockLoanEntity()}
        self.token_parameters = MagicMock()
        self.interest_rate_models = MagicMock()

    @property
    def get_protocol_name(self):
        return self.PROTOCOL_NAME

    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        # Mock implementation for the abstract method
        return None  # or returns a mock value
@pytest.mark.parametrize("state, expected", [
    (MockState("zkLend"), "zkLend"),
    (MockState("Nostra Alpha"), "Nostra Alpha"),
    (MockState("Nostra Mainnet"), "Nostra Mainnet"),
])
def test_get_protocol(state, expected):
    assert get_protocol(state) == expected


@pytest.mark.parametrize("state", [None, "invalid", 123])
def test_get_protocol_invalid(state):
    with pytest.raises(AttributeError):
        get_protocol(state)


@pytest.fixture
def mock_prices():
    return Prices({"ETH": 2000})


def test_get_loans_table_data(mock_prices):
    state = MockState("zkLend")
    df = get_loans_table_data(state, mock_prices)

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert set(df.columns) == {
        "User", "Protocol", "Collateral (USD)", "Risk-adjusted collateral (USD)",
        "Debt (USD)", "Health factor", "Standardized health factor", "Collateral", "Debt"
    }
    assert df.iloc[0]["User"] == "User1"
    assert df.iloc[0]["Collateral (USD)"] == 1000.0
    assert df.iloc[0]["Debt (USD)"] == 500.0
    assert df.iloc[0]["Health factor"] == 2.0


@pytest.mark.parametrize("protocol, token_addresses, expected", [
    ("zkLend", ["0x123"], (["0x123"], "felt_total_supply")),
    ("Nostra Alpha", ["0x456"], (["0x456"], "totalSupply")),
    ("Nostra Mainnet", ["0x789"], (["0x789"], "totalSupply")),
])
def test_get_supply_function_call_parameters(protocol, token_addresses, expected):
    assert get_supply_function_call_parameters(protocol, token_addresses) == expected


def test_get_supply_function_call_parameters_invalid():
    with pytest.raises(ValueError):
        get_supply_function_call_parameters("InvalidProtocol", ["0xabc"])