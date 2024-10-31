""" This module contains tests for the InitializerDBConnector class. """
import pytest
from data_handler.db.models import HashtackCollateralDebt, ZkLendCollateralDebt
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture(scope="function")
def sample_zklend_collateral_debt():
    """
    Sample zklend collateral debt for testing.
    :return: Sample zklend collateral debt
    """
    zklend_collateral_debt = ZkLendCollateralDebt(
        user_id="test_user",
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
        deposit={},
        collateral_enabled={"ETH": True},
    )
    return zklend_collateral_debt


@pytest.fixture(scope="function")
def sample_hashtack_collateral_debt():
    """
    Sample hashtack collateral debt for testing.
    :return: Sample hashtack collateral debt
    """
    hashtack_collateral_debt = HashtackCollateralDebt(
        user_id="test_user",
        loan_id="test_loan",
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
        original_collateral={"ETH": 120.0},
        borrowed_collateral={"ETH": 20.0},
        debt_category="test_category",
        version=1,
    )
    return hashtack_collateral_debt


def test_get_zklend_by_user_ids(mock_initializer_db_connector, sample_zklend_collateral_debt):
    """
    Test the get_zklend_by_user_ids method.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :param sample_zklend_collateral_debt: Sample zklend collateral debt
    :return: None
    """
    mock_initializer_db_connector.get_zklend_by_user_ids.return_value = [
        sample_zklend_collateral_debt
    ]
    result = mock_initializer_db_connector.get_zklend_by_user_ids(["test_user"])
    assert len(result) == 1
    assert result[0].user_id == "test_user"


def test_get_hashtack_by_loan_ids(mock_initializer_db_connector, sample_hashtack_collateral_debt):
    """
    Test the get_hashtack_by_loan_ids method.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :param sample_hashtack_collateral_debt: Sample hashtack collateral debt
    :return: None
    """
    mock_initializer_db_connector.get_hashtack_by_loan_ids.return_value = [
        sample_hashtack_collateral_debt
    ]
    result = mock_initializer_db_connector.get_hashtack_by_loan_ids(["test_loan"], 1)
    assert len(result) == 1
    assert result[0].loan_id == "test_loan"


def test_save_collateral_enabled_by_user(mock_initializer_db_connector):
    """
    Test the save_collateral_enabled_by_user method.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :return: None
    """
    mock_initializer_db_connector.save_collateral_enabled_by_user.return_value = None
    mock_initializer_db_connector.save_collateral_enabled_by_user(
        user_id="test_user",
        collateral_enabled={"ETH": True},
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
    )
    mock_initializer_db_connector.save_collateral_enabled_by_user.assert_called_once_with(
        user_id="test_user",
        collateral_enabled={"ETH": True},
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
    )


def test_save_debt_category(mock_initializer_db_connector):
    """
    Test the save_debt_category method.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :return: None
    """
    mock_initializer_db_connector.save_debt_category.return_value = None
    mock_initializer_db_connector.save_debt_category(
        user_id="test_user",
        loan_id="test_loan",
        debt_category="test_category",
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
        original_collateral={"ETH": 120.0},
        borrowed_collateral={"ETH": 20.0},
        version=1,
    )
    mock_initializer_db_connector.save_debt_category.assert_called_once_with(
        user_id="test_user",
        loan_id="test_loan",
        debt_category="test_category",
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
        original_collateral={"ETH": 120.0},
        borrowed_collateral={"ETH": 20.0},
        version=1,
    )


def test_get_zklend_by_user_ids_empty_list(mock_initializer_db_connector):
    """
    Test the get_zklend_by_user_ids method with an empty list of user IDs.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :return: None
    """
    mock_initializer_db_connector.get_zklend_by_user_ids.return_value = []
    result = mock_initializer_db_connector.get_zklend_by_user_ids(["not_exist_user"])
    assert len(result) == 0


def test_get_zklend_by_user_ids_db_error(mock_initializer_db_connector):
    """
    Test the get_zklend_by_user_ids method when a database error occurs.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :return: None
    """
    mock_initializer_db_connector.get_zklend_by_user_ids.side_effect = SQLAlchemyError(
        "Database error"
    )
    with pytest.raises(SQLAlchemyError):
        mock_initializer_db_connector.get_zklend_by_user_ids(["test_user"])


def test_save_collateral_enabled_by_user_update(
    mock_initializer_db_connector, sample_zklend_collateral_debt
):
    """
    Test the save_collateral_enabled_by_user method when updating an existing record.
    :param mock_initializer_db_connector: Mock InitializerDBConnector
    :param sample_zklend_collateral_debt: Sample zklend collateral debt
    :return: None
    """
    new_collateral_enabled = {"ETH": True}
    new_collateral = {"ETH": 100.0}
    new_debt = {"USDC": 1000.0}

    mock_initializer_db_connector.save_collateral_enabled_by_user(
        user_id="test_user",
        collateral_enabled=new_collateral_enabled,
        collateral=new_collateral,
        debt=new_debt,
    )

    assert sample_zklend_collateral_debt.collateral_enabled == new_collateral_enabled
    assert sample_zklend_collateral_debt.collateral == new_collateral
    assert sample_zklend_collateral_debt.debt == new_debt
