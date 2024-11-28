import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock, patch
from dashboard_app.helpers.tools import get_addresses, get_underlying_address
from dashboard_app.helpers.loans_table import get_protocol, get_supply_function_call_parameters
from data_handler.handlers import blockchain_call
from shared.types import Prices
from shared.constants import TOKEN_SETTINGS
from shared.state import State
from dashboard_app.helpers.protocol_stats import (
    get_general_stats,
    get_supply_stats,
    get_collateral_stats,
    get_debt_stats,
    get_utilization_stats,
)
from data_handler.handlers.loan_states.zklend.events import ZkLendState


@pytest.fixture
def mock_zklend_state():
    """Fixture to mock ZkLendState and its methods."""
    mock_state = MagicMock(spec=ZkLendState)
    mock_state.loan_entities = {
        "user1": MagicMock(),
        "user2": MagicMock(),
    }
    mock_state.compute_number_of_active_loan_entities.return_value = 2
    mock_state.compute_number_of_active_loan_entities_with_debt.return_value = 1
    mock_state.token_parameters = MagicMock()
    mock_state.interest_rate_models = MagicMock()
    return mock_state


@pytest.fixture
def mock_states():
    """Fixture for mock states with relevant methods."""
    state1 = MagicMock(spec=State)
    state1.loan_entities = {"user1": MagicMock(), "user2": MagicMock()}
    state1.compute_number_of_active_loan_entities.return_value = 2
    state1.compute_number_of_active_loan_entities_with_debt.return_value = 1
    state1.token_parameters = MagicMock()
    state1.interest_rate_models = MagicMock()
    
    state2 = MagicMock(spec=State)
    state2.loan_entities = {"user3": MagicMock()}
    state2.compute_number_of_active_loan_entities.return_value = 1
    state2.compute_number_of_active_loan_entities_with_debt.return_value = 1
    state2.token_parameters = MagicMock()
    state2.interest_rate_models = MagicMock()

    return [state1, state2]


def test_get_general_stats(mock_zklend_state):
    """Test get_general_stats with mocked ZkLendState."""
    loan_stats = {
        "zkLend": pd.DataFrame(
            {
                "Debt (USD)": [500, 700],
                "Risk-adjusted collateral (USD)": [1000, 1200],
                "Collateral (USD)": [1200, 1400],
            }
        )
    }

    with patch("dashboard_app.helpers.loans_table.get_protocol", return_value="zkLend"):
        df = get_general_stats([mock_zklend_state], loan_stats)
        assert "Protocol" in df.columns
        assert df.loc[0, "Protocol"] == "zkLend"
        assert df.loc[0, "Total debt (USD)"] == 1200  # Sum of loan_stats['Debt (USD)']


def test_get_collateral_stats(mock_zklend_state):
    """Test get_collateral_stats with mocked ZkLendState."""
    with patch("dashboard_app.helpers.loans_table.get_protocol", return_value="zkLend"):
        df = get_collateral_stats([mock_zklend_state])
        assert "Protocol" in df.columns
        assert "ETH collateral" in df.columns


def test_get_debt_stats(mock_zklend_state):
    """Test get_debt_stats with mocked ZkLendState."""
    with patch("dashboard_app.helpers.loans_table.get_protocol", return_value="zkLend"):
        df = get_debt_stats([mock_zklend_state])
        assert "Protocol" in df.columns
        assert "ETH debt" in df.columns

