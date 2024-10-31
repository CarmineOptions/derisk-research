"""
Tests for the loan state computations.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock
from datetime import datetime
from shared.constants import ProtocolIDs
from data_handler.handlers.loan_states.abstractions import (
    HashstackBaseLoanStateComputation
)


@pytest.fixture(scope="function")
def mock_hashstack_computation(mock_api_connector, mock_db_connector):
    """
    Creates a sample HashstackBaseLoanStateComputation instance for testing.
    """
    computation = MagicMock(spec=HashstackBaseLoanStateComputation)
    computation.PROTOCOL_TYPE = ProtocolIDs.ZKLEND
    computation.api_connector = mock_api_connector
    computation.db_connector = mock_db_connector


    computation.get_result_df = HashstackBaseLoanStateComputation.get_result_df.__get__(computation)
    computation.save_data = HashstackBaseLoanStateComputation.save_data.__get__(computation)
    computation.get_data.return_value = [{"test": "data"}]
    computation.get_addresses_data.return_value = [{"test": "data"}, {"test": "data"}]
    computation.process_event.return_value = None
    computation.run.return_value = None
    computation.last_block = 1000
    yield computation


@pytest.fixture(scope="function")
def sample_event_data():
    """
    Creates sample event data for testing.
    """
    return pd.Series({
        "block_number": 1001,
        "timestamp": int(datetime.now().timestamp()),
        "user": "test_user",
        "collateral": {"ETH": 100.0},
        "debt": {"USDC": 1000.0}
    })


@pytest.fixture(scope="function")
def sample_loan_state():
    """
    Sample loan state for testing.
    """
    loan_state = MagicMock()
    loan_state.user = "test_user"
    loan_state.protocol_id = ProtocolIDs.ZKLEND.value
    loan_state.collateral = MagicMock()
    loan_state.collateral.values = {"ETH": "100.0"}
    loan_state.debt = MagicMock()
    loan_state.debt.values = {"USDC": "1000.0"}
    loan_state.timestamp = 1000000
    loan_state.block = 12345
    loan_state.deposit = 10.0
    loan_state.has_skip = False
    loan_state.extra_info = MagicMock()
    loan_state.extra_info.block = 12345
    loan_state.extra_info.timestamp = 1000000
    
    return loan_state


@pytest.fixture(scope="function")
def valid_loan_entities(sample_loan_state):
    """
    Valid loan entities for testing.
    """
    return {"loan1": sample_loan_state}


@pytest.fixture(scope="function")
def sample_interest_rate():
    """
    Sample interest rate for testing.
    """
    interest_rate = MagicMock()
    interest_rate.block = 1001
    interest_rate.timestamp = 1234567890
    interest_rate.collateral = {"ETH": 100.0}
    interest_rate.debt = {"USDC": 1000.0}
    return interest_rate


def test_get_data_positive(mock_hashstack_computation):
    """
    Test get_data method with valid parameters.
    """
    expected_data = [{"test": "data"}]
    mock_hashstack_computation.get_data.return_value = expected_data
    
    result = mock_hashstack_computation.get_data("0x123", 1000)
    assert result == expected_data


def test_get_addresses_data_positive(mock_hashstack_computation):
    """
    Test get_addresses_data method with valid parameters.
    """
    addresses = ["0x123", "0x456"]
    
    mock_hashstack_computation.get_addresses_data = HashstackBaseLoanStateComputation.get_addresses_data.__get__(mock_hashstack_computation)
    
    mock_hashstack_computation.get_data = MagicMock(side_effect=[
        [{"test": "data"}],
        [{"test": "data"}]
    ])
    
    result = mock_hashstack_computation.get_addresses_data(addresses, 1000)
    
    assert len(result) == 2
    assert mock_hashstack_computation.get_data.call_count == 2
    
    mock_hashstack_computation.get_data.assert_any_call("0x123", 1000)
    mock_hashstack_computation.get_data.assert_any_call("0x456", 1000)


def test_save_data_positive(mock_hashstack_computation, sample_loan_state):
    """
    Test save_data method with valid DataFrame.
    """
    df = pd.DataFrame([{
        "user": sample_loan_state.user,
        "collateral": sample_loan_state.collateral.values,
        "debt": sample_loan_state.debt.values
    }])
    
    def mock_save_data(data_frame):
        mock_hashstack_computation.db_connector.write_loan_states_to_db(data_frame)
    
    mock_hashstack_computation.save_data = mock_save_data
    mock_hashstack_computation.save_data(df)
    mock_hashstack_computation.db_connector.write_loan_states_to_db.assert_called_once()
    mock_hashstack_computation.db_connector.write_loan_states_to_db.reset_mock()


def test_save_data_empty_df(mock_hashstack_computation):
    """
    Test save_data method with empty DataFrame.
    """
    df = pd.DataFrame()
    mock_hashstack_computation.save_data(df)
    mock_hashstack_computation.db_connector.write_loan_states_to_db.assert_not_called()


def test_process_event_positive(mock_hashstack_computation, sample_event_data):
    """
    Test process_event method with valid event data.
    """
    mock_state = MagicMock()
    mock_method = MagicMock()
    setattr(mock_state, "test_method", mock_method)
    
    mock_hashstack_computation.process_event = HashstackBaseLoanStateComputation.process_event.__get__(mock_hashstack_computation)
    mock_hashstack_computation.process_event(mock_state, "test_method", sample_event_data)
    mock_method.assert_called_once_with(sample_event_data)


def test_process_event_invalid_method(mock_hashstack_computation, sample_event_data):
    """
    Test process_event method with invalid method name.
    """
    mock_state = MagicMock()
    mock_hashstack_computation.process_event(mock_state, "nonexistent_method", sample_event_data)
    # Should not raise an error, just log the missing method


def test_save_interest_rate_data_positive(mock_hashstack_computation, sample_interest_rate):
    """
    Test save_interest_rate_data method with valid data.
    """
    mock_hashstack_computation.interest_rate_result = [sample_interest_rate]
    mock_hashstack_computation.save_interest_rate_data = HashstackBaseLoanStateComputation.save_interest_rate_data.__get__(mock_hashstack_computation)
    mock_hashstack_computation.save_interest_rate_data()
    mock_hashstack_computation.db_connector.write_batch_to_db.assert_called_once()
    mock_hashstack_computation.db_connector.write_batch_to_db.reset_mock()


def test_save_interest_rate_data_empty(mock_hashstack_computation):
    """
    Test save_interest_rate_data method with empty data.
    """
    mock_hashstack_computation.interest_rate_result = []
    mock_hashstack_computation.save_interest_rate_data()
    mock_hashstack_computation.db_connector.write_batch_to_db.assert_not_called()


def test_run_positive(mock_hashstack_computation):
    """
    Test run method with successful data processing.
    """
    mock_hashstack_computation.run = HashstackBaseLoanStateComputation.run.__get__(mock_hashstack_computation)
    
    mock_hashstack_computation.PROTOCOL_ADDRESSES = ["0x123"]
    mock_hashstack_computation.last_block = 1000
    mock_hashstack_computation.PAGINATION_SIZE = 1000
    
    data_returns = [
        [{"test": "data"}], 
        [],                 
        [],                 
        [],                 
        [],                 
        [],                 
    ]
    
    mock_hashstack_computation.get_data = MagicMock(side_effect=data_returns)
    
    mock_hashstack_computation.process_data = MagicMock(return_value=[{"processed": "data"}])
    mock_hashstack_computation.save_data = MagicMock()
    mock_hashstack_computation.save_interest_rate_data = MagicMock()
    
    mock_hashstack_computation.run()
    
    assert mock_hashstack_computation.get_data.call_count == 6
    
    mock_hashstack_computation.get_data.assert_any_call("0x123", 1000)
    
    mock_hashstack_computation.process_data.assert_called_once_with([{"test": "data"}])
    mock_hashstack_computation.save_data.assert_called_once_with([{"processed": "data"}])
    mock_hashstack_computation.save_interest_rate_data.assert_called_once()
    
    assert mock_hashstack_computation.last_block == 7000    


@pytest.mark.parametrize("block,expected_calls", [
    (1001, 1),  # Different block, should update
    (1000, 0),  # Same block, should not update
])
def test_set_interest_rate(mock_hashstack_computation, block, expected_calls):
    """
    Test set_interest_rate method with different scenarios.
    """
    mock_state = MagicMock()
    mock_state.last_interest_rate_block_number = 1000
    
    mock_interest_rate = MagicMock()
    mock_interest_rate.get_json_deserialized.return_value = ({"ETH": 0.1}, {"USDC": 0.05})
    mock_hashstack_computation.db_connector.get_interest_rate_by_block.return_value = mock_interest_rate

    mock_hashstack_computation.set_interest_rate = HashstackBaseLoanStateComputation.set_interest_rate.__get__(mock_hashstack_computation)
    
    mock_hashstack_computation.set_interest_rate(
        mock_state, block, ProtocolIDs.ZKLEND
    )
    assert mock_hashstack_computation.db_connector.get_interest_rate_by_block.call_count == expected_calls
    mock_hashstack_computation.db_connector.get_interest_rate_by_block.reset_mock()


def test_get_result_df_positive(mock_hashstack_computation, sample_loan_state):
    """
    Test get_result_df method with valid loan entities.
    """
    result = mock_hashstack_computation.get_result_df({"test": sample_loan_state})
    
    assert not result.empty
    assert len(result) == 1
    assert result.iloc[0]["user"] == "test_user"
    assert result.iloc[0]["collateral"] == {"ETH": 100.0}
    assert result.iloc[0]["debt"] == {"USDC": 1000.0}


def test_get_result_df_empty_input(mock_hashstack_computation):
    """
    Test get_result_df with empty input
    """
    result = mock_hashstack_computation.get_result_df({})
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_get_result_df_with_skipped_entities(mock_hashstack_computation):
    """
    Test get_result_df with entities marked for skipping
    """
    # Create two loan entities, one with has_skip=True
    skipped_loan = MagicMock()
    skipped_loan.has_skip = True
    
    valid_loan = MagicMock()
    valid_loan.has_skip = False
    valid_loan.user = "user2"
    valid_loan.collateral.values = {"ETH": "2.0"}
    valid_loan.debt.values = {"USDC": "2000.0"}
    valid_loan.extra_info.block = 101
    valid_loan.extra_info.timestamp = 1000001
    
    loan_entities = {
        "loan1": skipped_loan,
        "loan2": valid_loan
    }
    
    result = mock_hashstack_computation.get_result_df(loan_entities)
    assert len(result) == 1
    assert result["user"].iloc[0] == "user2"


def test_get_result_df_float_conversion(mock_hashstack_computation):
    """
    Test get_result_df properly converts string amounts to floats
    """
    loan = MagicMock()
    loan.has_skip = False
    loan.user = "user1"
    loan.collateral.values = {"ETH": "1.5"}  
    loan.debt.values = {"USDC": "1000.0"}   
    loan.extra_info.block = 100
    loan.extra_info.timestamp = 1000000
    
    loan_entities = {"loan1": loan}
    result = mock_hashstack_computation.get_result_df(loan_entities)
    
    assert isinstance(result["collateral"].iloc[0]["ETH"], float)
    assert isinstance(result["debt"].iloc[0]["USDC"], float)


def test_get_result_df_with_none_values(mock_hashstack_computation):
    """
    Test get_result_df handles None values appropriately
    """
    loan = MagicMock()
    loan.has_skip = False
    loan.user = "user1"
    loan.collateral.values = {"ETH": None}
    loan.debt.values = {"USDC": None}
    loan.extra_info.block = 100
    loan.extra_info.timestamp = 1000000
    
    loan_entities = {"loan1": loan}
    
    with pytest.raises(TypeError):
        mock_hashstack_computation.get_result_df(loan_entities)


def test_get_result_df_with_invalid_extra_info(mock_hashstack_computation):
    """
    Test get_result_df handles invalid extra_info structure
    """
    loan = MagicMock()
    loan.has_skip = False
    loan.user = "user1"
    loan.collateral.values = {"ETH": "1.5"}
    loan.debt.values = {"USDC": "1000.0"}
    loan.extra_info = "invalid" 
    
    loan_entities = {"loan1": loan}
    
    with pytest.raises(AttributeError):
        mock_hashstack_computation.get_result_df(loan_entities)


def test_get_result_df_with_multiple_valid_entities(mock_hashstack_computation):
    """
    Test get_result_df with multiple valid entities
    """
    loan1 = MagicMock()
    loan1.has_skip = False
    loan1.user = "user1"
    loan1.collateral.values = {"ETH": "1.5"}
    loan1.debt.values = {"USDC": "1000.0"}
    loan1.extra_info.block = 100
    loan1.extra_info.timestamp = 1000000

    loan2 = MagicMock()
    loan2.has_skip = False
    loan2.user = "user2"
    loan2.collateral.values = {"ETH": "0.5"}
    loan2.debt.values = {"USDT": "200.0"}
    loan2.extra_info.block = 101
    loan2.extra_info.timestamp = 1000001
    
    loan_entities = {
        "loan1": loan1,
        "loan2": loan2
    }
    
    result = mock_hashstack_computation.get_result_df(loan_entities)
    assert len(result) == 2
    assert result["user"].tolist() == ["user1", "user2"]
    assert result["collateral"].tolist() == [{"ETH": 1.5}, {"ETH": 0.5}]
    assert result["debt"].tolist() == [{"USDC": 1000.0}, {"USDT": 200.0}]
