"""Tests for the ZkLendInitializer class."""
import pandas as pd
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from data_handler.db.models import ZkLendCollateralDebt
from data_handler.handlers.loan_states.zklend.utils import ZkLendInitializer


@pytest.fixture(autouse=True)
def mock_db_session():
    """Mock database session to prevent actual database connections."""
    with patch('data_handler.db.crud.Session') as mock_session:
        yield mock_session


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
def initializer(mock_zklend_state, mock_initializer_db_connector):
    """Create ZkLendInitializer instance with mocked dependencies."""
    instance = ZkLendInitializer(mock_zklend_state)
    instance.db_connector = mock_initializer_db_connector
    return instance


@pytest.fixture
def sample_df():
    """Sample DataFrame for testing."""
    return pd.DataFrame([
        {"key_name": "CollateralEnabled", "data": ["user1"]},
        {"key_name": "Repayment", "data": ["event", "user2"]},
        {"key_name": "TreasuryUpdate", "data": ["some_data"]},
        {"key_name": "Liquidation", "data": ["event", "user3"]}
    ])


def test_select_element_valid_cases(initializer, sample_df):
    """Test _select_element method with valid inputs."""
    # Test CollateralEnabled case
    result = initializer._select_element(sample_df.iloc[0])
    assert result == "user1"

    # Test Repayment case
    result = initializer._select_element(sample_df.iloc[1])
    assert result == "user2"

    # Test Liquidation case
    result = initializer._select_element(sample_df.iloc[3])
    assert result == "user3"


def test_get_user_ids_from_df_with_valid_data(initializer, sample_df):
    """Test get_user_ids_from_df method with valid DataFrame."""
    result = initializer.get_user_ids_from_df(sample_df)

    assert isinstance(result, list)
    assert len(result) == 3
    assert set(result) == {"user1", "user2", "user3"}
    assert len(set(result)) == len(result)  # No duplicates


def test_set_last_loan_states_per_users_success(
    initializer,
    mock_initializer_db_connector,
    mock_zklend_state,
    sample_loan_state
):
    """Test successful setting of loan states."""
    mock_initializer_db_connector.get_zklend_by_user_ids.return_value = [sample_loan_state]

    initializer.set_last_loan_states_per_users(["user1"])

    mock_initializer_db_connector.get_zklend_by_user_ids.assert_called_once_with(["user1"])
    user_loan_state = mock_zklend_state.loan_entities["user1"]
    assert user_loan_state.collateral_enabled.values == {"ETH": True}
    assert user_loan_state.collateral.values == {"ETH": Decimal("100.0")}
    assert user_loan_state.debt.values == {"USDC": Decimal("1000.0")}


def test_convert_float_to_decimal_valid_data(initializer):
    """Test _convert_float_to_decimal with valid input."""
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


def test_select_element_invalid_cases(initializer):
    """Test _select_element method with invalid inputs."""
    # Test with empty DataFrame row
    empty_row = pd.Series({"key_name": "", "data": []})
    assert initializer._select_element(empty_row) is None

    # Test with invalid key_name
    invalid_row = pd.Series({"key_name": "InvalidEvent", "data": ["user1"]})
    assert initializer._select_element(invalid_row) is None

    # Test with missing data
    missing_data_row = pd.Series({"key_name": "Repayment"})
    with pytest.raises(KeyError):
        initializer._select_element(missing_data_row)


def test_get_user_ids_from_df_empty_df(initializer):
    """Test get_user_ids_from_df with empty DataFrame."""
    empty_df = pd.DataFrame(columns=["key_name", "data"])
    result = initializer.get_user_ids_from_df(empty_df)
    assert isinstance(result, list)
    assert len(result) == 0


def test_set_last_loan_states_per_users_db_error(initializer, mock_initializer_db_connector):
    """Test set_last_loan_states_per_users with database error."""
    mock_initializer_db_connector.get_zklend_by_user_ids.side_effect = SQLAlchemyError("Database error")

    with pytest.raises(SQLAlchemyError):
        initializer.set_last_loan_states_per_users(["user1"])


def test_convert_float_to_decimal_invalid_data(initializer):
    """Test _convert_float_to_decimal with invalid inputs."""
    # Test with None
    assert initializer._convert_float_to_decimal(None) is None

    # Test with empty dict
    assert initializer._convert_float_to_decimal({}) == {}

    # Test with invalid values
    invalid_data = {"ETH": "not_a_number"}
    with pytest.raises(TypeError):
        initializer._convert_float_to_decimal(invalid_data)


def test_set_last_loan_states_per_users_user_not_found(
    initializer,
    mock_initializer_db_connector
):
    """Test set_last_loan_states_per_users when user is not found."""
    mock_initializer_db_connector.get_zklend_by_user_ids.return_value = []

    initializer.set_last_loan_states_per_users(["nonexistent_user"])
    mock_initializer_db_connector.get_zklend_by_user_ids.assert_called_once_with(["nonexistent_user"])


def test_get_user_ids_from_df_malformed_data(initializer):
    """Test get_user_ids_from_df with malformed DataFrame."""
    malformed_df = pd.DataFrame([
        {"wrong_column": "CollateralEnabled", "other_column": ["user1"]}
    ])

    with pytest.raises(KeyError):
        initializer.get_user_ids_from_df(malformed_df)