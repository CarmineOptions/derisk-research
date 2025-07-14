"""
Unit tests for loans table functionality.
"""

from unittest.mock import MagicMock
import pytest
import pandas as pd

pytest.importorskip("shared")
from helpers.loans_table import (
    get_protocol,
    get_loans_table_data,
    get_supply_function_call_parameters,
)
from shared.state import State
from shared.custom_types import Prices


class MockLoanEntity:
    """Mock class representing a loan entity for testing purposes."""

    def __init__(self):
        """Initialize a mock loan entity with collateral and debt."""
        self.collateral = {"ETH": 1000}
        self.debt = {"ETH": 500}

    def compute_collateral_usd(self, *_args, **_kwargs):
        """Mock computation for collateral value in USD."""
        return 1000.0

    def compute_debt_usd(self, *_args, **_kwargs):
        """Mock computation for debt value in USD."""
        return 500.0

    def compute_health_factor(self, *_args, **_kwargs):
        """Mock computation for health factor."""
        return 2.0

    def get_collateral_str(self, *_args, **_kwargs):
        """Mock retrieval of collateral string representation."""
        return "100 ETH"

    def get_debt_str(self, *_args, **_kwargs):
        """Mock retrieval of debt string representation."""
        return "50 USDC"


class MockState(State):
    """Mock state class for loan protocol testing."""

    def __init__(self, protocol_name):
        """Initialize the mock state with a protocol name and mock loan entities."""
        super().__init__(loan_entity_class=MockLoanEntity)
        self.protocol_name = protocol_name
        self.loan_entities = {"User1": MockLoanEntity()}
        self.token_parameters = MagicMock()
        self.interest_rate_models = MagicMock()

    @property
    def get_protocol_name(self):
        """Retrieve the protocol name."""
        return self.protocol_name

    def compute_liquidable_debt_at_price(self, *_args, **_kwargs):
        """Mock implementation for abstract method."""
        return None  # Returns a mock value


@pytest.mark.parametrize(
    "state, expected",
    [
        (MockState("zkLend"), "zkLend"),
        (MockState("Nostra Alpha"), "Nostra Alpha"),
        (MockState("Nostra Mainnet"), "Nostra Mainnet"),
    ],
)
def test_get_protocol(state, expected):
    """Test protocol retrieval for different states."""
    assert get_protocol(state) == expected


@pytest.mark.parametrize("state", [None, "invalid", 123])
def test_get_protocol_invalid(state):
    """Test get_protocol with invalid input, expecting AttributeError."""
    with pytest.raises(AttributeError):
        get_protocol(state)


@pytest.fixture
def mock_prices_fixture():
    """Fixture providing mock price data."""
    return Prices({"ETH": 2000})


def test_get_loans_table_data(mock_prices_fixture):
    """Test loans table data generation."""
    state = MockState("zkLend")
    loan_data_frame = get_loans_table_data(state, mock_prices_fixture)

    assert isinstance(loan_data_frame, pd.DataFrame)
    assert not loan_data_frame.empty
    assert set(loan_data_frame.columns) == {
        "User",
        "Protocol",
        "Collateral (USD)",
        "Risk-adjusted collateral (USD)",
        "Debt (USD)",
        "Health factor",
        "Standardized health factor",
        "Collateral",
        "Debt",
    }
    assert loan_data_frame.iloc[0]["User"] == "User1"
    assert loan_data_frame.iloc[0]["Collateral (USD)"] == 1000.0
    assert loan_data_frame.iloc[0]["Debt (USD)"] == 500.0
    assert loan_data_frame.iloc[0]["Health factor"] == 2.0


@pytest.mark.parametrize(
    "protocol, token_addresses, expected",
    [
        ("zkLend", ["0x123"], (["0x123"], "felt_total_supply")),
        ("Nostra Alpha", ["0x456"], (["0x456"], "totalSupply")),
        ("Nostra Mainnet", ["0x789"], (["0x789"], "totalSupply")),
    ],
)
def test_get_supply_function_call_parameters(protocol, token_addresses, expected):
    """Test supply function call parameter retrieval for different protocols."""
    assert get_supply_function_call_parameters(protocol, token_addresses) == expected


def test_get_supply_function_call_parameters_invalid():
    """Test supply function call retrieval with an invalid protocol, expecting ValueError."""
    with pytest.raises(ValueError):
        get_supply_function_call_parameters("InvalidProtocol", ["0xabc"])
