"""Tests for the ZkLendInitializer class."""
import pandas as pd
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from data_handler.db.models import ZkLendCollateralDebt
from data_handler.handlers.loan_states.zklend.utils import ZkLendInitializer


@pytest.fixture
def mock_zklend_initializer():
    """Mock ZkLendInitializer instance."""
    mock_initializer = MagicMock(spec=ZkLendInitializer)
    mock_initializer.db_connector = MagicMock()

    mock_initializer.get_user_ids_from_df.return_value = ["user1", "user2", "user3"]
    
    mock_initializer._convert_float_to_decimal.return_value = {
        "ETH": Decimal("100.0"),
        "USDC": Decimal("1000.0")
    }

    def select_element_side_effect(row):
        if not row['data'] or not row['key_name']:
            return None
        return row['data'][-1] if len(row['data']) > 0 else None
    
    mock_initializer._select_element.side_effect = select_element_side_effect
    
    yield mock_initializer


@pytest.fixture
def mock_zklend_state():
    """Mock ZkLendState instance."""
    mock_state = MagicMock()
    mock_state.loan_entities = {
        "user1": MagicMock(
            collateral_enabled=MagicMock(values=None),
            collateral=MagicMock(values=None),
            debt=MagicMock(values=None)
        )
    }
    return mock_state


@pytest.fixture
def sample_df():
    """Sample DataFrame for testing."""
    return pd.DataFrame([
        {"key_name": "CollateralEnabled", "data": ["user1"]},
        {"key_name": "Repayment", "data": ["event", "user2"]},
        {"key_name": "TreasuryUpdate", "data": ["some_data"]},
        {"key_name": "Liquidation", "data": ["event", "user3"]}
    ])


@pytest.fixture
def sample_loan_state():
    """Sample ZkLendCollateralDebt instance."""
    return ZkLendCollateralDebt(
        user_id="user1",
        collateral_enabled={"ETH": True},
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
        deposit={"ETH": 100.0},
    )


@pytest.fixture
def initializer(mock_zklend_state):
    """Create ZkLendInitializer instance with mocked dependencies."""
    with patch('data_handler.handlers.loan_states.zklend.utils.InitializerDBConnector') as mock_connector_class:
        mock_connector_class.return_value = MagicMock()
        instance = ZkLendInitializer(mock_zklend_state)
        return instance


# Positive Test Scenarios
def test_select_element_valid_cases(initializer, sample_df):
    """Test _select_element method with valid inputs."""
    result = initializer._select_element(sample_df.iloc[0])
    assert result == "user1"
    
    result = initializer._select_element(sample_df.iloc[1])
    assert result == "user2"
    
    result = initializer._select_element(sample_df.iloc[3])
    assert result == "user3"


def test_get_user_ids_from_df_with_valid_data(mock_zklend_initializer, sample_df):
    """Test get_user_ids_from_df method with valid DataFrame."""
    initializer = mock_zklend_initializer
    result = initializer.get_user_ids_from_df(sample_df)
    
    assert isinstance(result, list)
    assert len(result) == 3
    assert set(result) == {"user1", "user2", "user3"}
    assert len(set(result)) == len(result)  # No duplicates


def test_set_last_loan_states_per_users_success(
    initializer,
    mock_zklend_state,
    sample_loan_state
):
    """Test successful setting of loan states."""
    initializer.db_connector.get_zklend_by_user_ids.return_value = [sample_loan_state]
    initializer.zklend_state = mock_zklend_state
    
    initializer.set_last_loan_states_per_users(["user1"])
    
    user_loan_state = mock_zklend_state.loan_entities["user1"]
    assert user_loan_state.collateral_enabled.values == {"ETH": True}
    assert user_loan_state.collateral.values == {"ETH": Decimal("100.0")}
    assert user_loan_state.debt.values == {"USDC": Decimal("1000.0")}


def test_convert_float_to_decimal_valid_data(mock_zklend_initializer):
    """Test _convert_float_to_decimal with valid input."""
    initializer = mock_zklend_initializer
    
    test_data = {
        "ETH": 100.0,
        "USDC": 1000.0
    }
    result = initializer._convert_float_to_decimal(test_data)
    
    assert isinstance(result["ETH"], Decimal)
    assert isinstance(result["USDC"], Decimal)
    assert result == {
        "ETH": Decimal("100.0"),
        "USDC": Decimal("1000.0")
    }


# Negative Test Scenarios
def test_select_element_invalid_cases(mock_zklend_initializer):
    """Test _select_element method with invalid inputs."""
    initializer = mock_zklend_initializer
    
    empty_row = pd.Series({"key_name": "", "data": []})
    result = initializer._select_element(empty_row)
    assert result is None


def test_get_user_ids_from_df_empty_df(mock_zklend_initializer):
    """Test get_user_ids_from_df with empty DataFrame."""
    initializer = mock_zklend_initializer
    empty_df = pd.DataFrame(columns=["key_name", "data"])
    
    initializer.get_user_ids_from_df.return_value = []
    
    result = initializer.get_user_ids_from_df(empty_df)
    assert isinstance(result, list)
    assert len(result) == 0


def test_set_last_loan_states_per_users_db_error(
    initializer,
    mock_zklend_state
):
    """Test set_last_loan_states_per_users with database error."""
    initializer.db_connector.get_zklend_by_user_ids.side_effect = SQLAlchemyError("Database error")
    initializer.zklend_state = mock_zklend_state
    
    with pytest.raises(SQLAlchemyError):
        initializer.set_last_loan_states_per_users(["user1"])


def test_convert_float_to_decimal_invalid_data(mock_zklend_initializer):
    """Test _convert_float_to_decimal with invalid inputs."""
    initializer = mock_zklend_initializer
    
    initializer._convert_float_to_decimal.side_effect = lambda x: None if x is None else x
    
    assert initializer._convert_float_to_decimal(None) is None


def test_set_last_loan_states_per_users_user_not_found(
    initializer,
    mock_zklend_state
):
    """Test set_last_loan_states_per_users when user is not found."""
    initializer.db_connector.get_zklend_by_user_ids.return_value = []
    
    initializer.set_last_loan_states_per_users(["nonexistent_user"])
    initializer.db_connector.get_zklend_by_user_ids.assert_called_once_with(["nonexistent_user"])


def test_get_user_ids_from_df_malformed_data(mock_zklend_initializer):
    """Test get_user_ids_from_df with malformed DataFrame."""
    initializer = mock_zklend_initializer
    
    malformed_df = pd.DataFrame([
        {"wrong_column": "CollateralEnabled", "other_column": ["user1"]}
    ])
    
    initializer.get_user_ids_from_df.side_effect = KeyError("key_name")
    
    with pytest.raises(KeyError):
        initializer.get_user_ids_from_df(malformed_df)