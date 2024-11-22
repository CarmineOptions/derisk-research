import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from decimal import Decimal
from data_handler.db.models import ZkLendCollateralDebt
from apps.data_handler.handlers.loan_states.zklend.utils import ZkLendInitializer


@pytest.fixture
def mock_zklend_state():
    mock_state = MagicMock()
    mock_state.loan_entities = {}
    return mock_state


@pytest.fixture
def mock_db_connector():
    with patch('data_handler.db.crud.InitializerDBConnector') as mock_connector:
        instance = mock_connector.return_value
        instance.get_zklend_by_user_ids.return_value = [
            ZkLendCollateralDebt(
                user_id="user_1",
                collateral_enabled={"ETH": True},
                collateral={"ETH": 1.0},
                debt={"USDC": 500.0}
            )
        ]
        yield instance


@pytest.fixture
def zk_lend_initializer(mock_zklend_state, mock_db_connector):
    return ZkLendInitializer(mock_zklend_state)


def test_select_element_treasury_update():
    row = pd.Series({"key_name": "TreasuryUpdate", "data": [1, 2, 3]})
    result = ZkLendInitializer._select_element(row)
    assert result is None


def test_select_element_collateral_enabled():
    row = pd.Series({"key_name": "CollateralEnabled", "data": ["user_1"]})
    result = ZkLendInitializer._select_element(row)
    assert result == "user_1"


def test_select_element_other_keys():
    row = pd.Series({"key_name": "OtherKey", "data": ["unused", "user_2"]})
    result = ZkLendInitializer._select_element(row)
    assert result == "user_2"


def test_get_user_ids_from_df(zk_lend_initializer):
    data = [
        {"key_name": "CollateralEnabled", "data": ["user_1"]},
        {"key_name": "OtherKey", "data": ["unused", "user_2"]},
        {"key_name": "OtherKey", "data": ["unused", "user_1"]},
    ]
    df = pd.DataFrame(data)
    user_ids = zk_lend_initializer.get_user_ids_from_df(df)
    assert set(user_ids) == {"user_1", "user_2"}


def test_set_last_loan_states_per_users(zk_lend_initializer, mock_zklend_state, mock_db_connector):
    mock_zklend_state.loan_entities["user_1"] = MagicMock()
    zk_lend_initializer.set_last_loan_states_per_users(["user_1"])
    
    loan_entity = mock_zklend_state.loan_entities["user_1"]
    assert loan_entity.collateral_enabled.values == {"ETH": True}
    assert loan_entity.collateral.values == {"ETH": Decimal("1.0")}
    assert loan_entity.debt.values == {"USDC": Decimal("500.0")}


def test_set_loan_state_per_user(zk_lend_initializer, mock_zklend_state):
    loan_state = ZkLendCollateralDebt(
        user_id="user_1",
        collateral_enabled={"ETH": True},
        collateral={"ETH": 1.0},
        debt={"USDC": 500.0}
    )
    mock_zklend_state.loan_entities["user_1"] = MagicMock()
    zk_lend_initializer._set_loan_state_per_user(loan_state)

    loan_entity = mock_zklend_state.loan_entities["user_1"]
    assert loan_entity.collateral_enabled.values == {"ETH": True}
    assert loan_entity.collateral.values == {"ETH": Decimal("1.0")}
    assert loan_entity.debt.values == {"USDC": Decimal("500.0")}


def test_convert_float_to_decimal():
    data = {"ETH": 1.0, "USDC": 500.0}
    result = ZkLendInitializer._convert_float_to_decimal(data)
    assert result == {"ETH": Decimal("1.0"), "USDC": Decimal("500.0")}


def test_convert_float_to_decimal_none():
    result = ZkLendInitializer._convert_float_to_decimal(None)
    assert result is None
