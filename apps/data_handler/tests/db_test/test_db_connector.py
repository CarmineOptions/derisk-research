"""
This module contains the tests for the DBConnector.
"""

import pytest
from data_handler.db.models import (
    HashtackCollateralDebt,
    InterestRate,
    LoanState,
    OrderBookModel,
)
from shared.constants import ProtocolIDs
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture(scope="function")
def sample_loan_state(mock_db_connector):
    """
    Sample loan state for testing.
    :param mock_db_connector: Mock DBConnector
    :return: Sample loan state
    """
    loan_state = LoanState(
        user="test_user",
        protocol_id=ProtocolIDs.ZKLEND.value,
        collateral=100.0,
        debt=50.0,
        timestamp=1000000,
        block=12345,
        deposit=10.0,
    )
    mock_db_connector.write_to_db.return_value = loan_state
    return loan_state


@pytest.fixture(scope="function")
def sample_batch_loan_states():
    """
    Sample batch loan states for testing.
    :param mock_db_connector: Mock DBConnector
    :return: Sample batch loan states
    """
    batch_loan_states = [
        LoanState(
            user=f"user{i}",
            protocol_id=ProtocolIDs.ZKLEND.value,
            collateral=100.0,
            debt=50.0,
            timestamp=1000000,
            block=12345,
            deposit=10.0,
        ) for i in range(3)
    ]
    return batch_loan_states


@pytest.fixture(scope="function")
def sample_hashstack_loan_state():
    """
    Sample hashstack loan state for testing.
    :param mock_db_connector: Mock DBConnector
    :return: Sample hashstack loan state
    """
    return HashtackCollateralDebt(
        user_id="test_user",
        loan_id=1,
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
        original_collateral={"ETH": 120.0},
        borrowed_collateral={"ETH": 20.0},
        debt_category="test_category",
        version=1,
    )


@pytest.fixture(scope="function")
def sample_interest_rate():
    """
    Sample interest rate for testing.
    :return: Sample interest rate
    """
    interest_rate = InterestRate(
        collateral={"ETH": 100.0},
        debt={"USDC": 1000.0},
    )
    return interest_rate


def test_write_to_db_positive(mock_db_connector, sample_loan_state):
    """
    Test the write_to_db method.
    :param mock_db_connector: Mock DBConnector
    :param sample_loan_state: Sample loan state
    :return: None
    """
    result = mock_db_connector.write_to_db(sample_loan_state)
    assert result.user == "test_user"
    mock_db_connector.write_to_db.assert_called_once_with(sample_loan_state)


def test_write_to_db_error(mock_db_connector):
    """
    Test the write_to_db method with an error.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    mock_db_connector.write_to_db.side_effect = SQLAlchemyError("Database error")
    with pytest.raises(SQLAlchemyError):
        mock_db_connector.write_to_db(LoanState())


def test_get_object_positive(mock_db_connector, sample_loan_state):
    """
    Test the get_object method.
    :param mock_db_connector: Mock DBConnector
    :param sample_loan_state: Sample loan state
    :return: None
    """
    mock_db_connector.get_object.return_value = sample_loan_state
    result = mock_db_connector.get_object(LoanState, sample_loan_state.id)
    assert result.user == "test_user"
    mock_db_connector.get_object.assert_called_once_with(LoanState, sample_loan_state.id)


def test_get_object_not_found(mock_db_connector):
    """
    Test the get_object method with a non-existent object.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    mock_db_connector.get_object.return_value = None
    result = mock_db_connector.get_object(LoanState, "non_existent_id")
    assert result is None


def test_delete_object_positive(mock_db_connector, sample_loan_state):
    """
    Test the delete_object method.
    :param mock_db_connector: Mock DBConnector
    :param sample_loan_state: Sample loan state
    :return: None
    """
    mock_db_connector.delete_object.return_value = None
    mock_db_connector.delete_object(LoanState, sample_loan_state.id)
    mock_db_connector.delete_object.assert_called_once_with(LoanState, sample_loan_state.id)


def test_get_latest_block_loans(mock_db_connector):
    """
    Test the get_latest_block_loans method.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    mock_loans = [LoanState(user="user1"), LoanState(user="user2")]
    mock_db_connector.get_latest_block_loans.return_value = mock_loans
    result = mock_db_connector.get_latest_block_loans()
    assert len(result) == 2
    assert result[0].user == "user1"
    assert result[1].user == "user2"


def test_get_last_block(mock_db_connector):
    """
    Test the get_last_block method.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    mock_db_connector.get_last_block.return_value = 12345
    result = mock_db_connector.get_last_block(ProtocolIDs.ZKLEND)
    assert result == 12345
    mock_db_connector.get_last_block.assert_called_once_with(ProtocolIDs.ZKLEND)


def test_write_loan_states_to_db(mock_db_connector):
    """
    Test the write_loan_states_to_db method.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    loan_states = [LoanState(user=f"user{i}") for i in range(3)]
    mock_db_connector.write_loan_states_to_db(loan_states)
    mock_db_connector.write_loan_states_to_db.assert_called_once_with(loan_states)


def test_get_latest_order_book(mock_db_connector):
    """
    Test the get_latest_order_book method.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    mock_order_book = OrderBookModel(dex="test_dex", token_a="tokenA", token_b="tokenB")
    mock_db_connector.get_latest_order_book.return_value = mock_order_book
    result = mock_db_connector.get_latest_order_book("test_dex", "tokenA", "tokenB")
    assert result.dex == "test_dex"
    assert result.token_a == "tokenA"
    assert result.token_b == "tokenB"


def test_get_last_interest_rate_record_by_protocol_id(mock_db_connector):
    """
    Test the get_last_interest_rate_record_by_protocol_id method.
    :param mock_db_connector: Mock DBConnector
    :return: None
    """
    mock_interest_rate = InterestRate(protocol_id=ProtocolIDs.ZKLEND.value, block=12345)
    mock_db_connector.get_last_interest_rate_record_by_protocol_id.return_value = (
        mock_interest_rate
    )
    result = mock_db_connector.get_last_interest_rate_record_by_protocol_id(ProtocolIDs.ZKLEND)
    assert result.protocol_id == ProtocolIDs.ZKLEND.value
    assert result.block == 12345


def test_write_batch_to_db(mock_db_connector, sample_batch_loan_states):
    """
    Test the write_batch_to_db method.
    :param mock_db_connector: Mock DBConnector
    :param sample_batch_loan_states: Sample batch loan states
    :return: None
    """
    mock_db_connector.write_batch_to_db(sample_batch_loan_states)
    mock_db_connector.write_batch_to_db.assert_called_once_with(sample_batch_loan_states)


def test_get_loans(mock_db_connector, sample_batch_loan_states):
    """
    Test the get_loans method.
    :param mock_db_connector: Mock DBConnector
    :param sample_batch_loan_states: Sample batch loan states
    :return: None
    """
    mock_db_connector.get_loans.return_value = sample_batch_loan_states
    result = mock_db_connector.get_loans(LoanState)
    assert len(result) == 3
    assert result[0].user == "user0"
    assert result[1].user == "user1"
    assert result[2].user == "user2"


def test_get_last_hashstack_loan_state(mock_db_connector, sample_hashstack_loan_state):
    """
    Test the get_last_hashstack_loan_state method.
    :param mock_db_connector: Mock DBConnector
    :param sample_hashstack_loan_state: Sample hashstack loan state
    :return: None
    """
    mock_db_connector.get_last_hashstack_loan_state.return_value = (sample_hashstack_loan_state)
    result = mock_db_connector.get_last_hashstack_loan_state("test_user")
    assert result.user_id == "test_user"
    assert result.loan_id == 1
    assert result.collateral == {"ETH": 100.0}
    assert result.debt == {"USDC": 1000.0}


def test_get_interest_rate_by_block(mock_db_connector, sample_interest_rate):
    """
    Test the get_interest_rate_by_block method.
    :param mock_db_connector: Mock DBConnector
    :param sample_interest_rate: Sample interest rate
    :return: None
    """
    mock_db_connector.get_interest_rate_by_block.return_value = sample_interest_rate
    result = mock_db_connector.get_interest_rate_by_block(12345, ProtocolIDs.ZKLEND)
    assert result.collateral == {"ETH": 100.0}
    assert result.debt == {"USDC": 1000.0}
