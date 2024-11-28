import pytest
from shared.state import State


class MockLoanEntity:
    """Mock loan entity for testing"""
    pass


class MockState(State):
    def __init__(self):
        super().__init__(loan_entity_class=MockLoanEntity)
    
    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        return None


def test_state_without_protocol_name():
    """Test that accessing get_protocol_name raises NotImplementedError when PROTOCOL_NAME is not set"""
    mock_state = MockState()
    with pytest.raises(NotImplementedError):
        _ = mock_state.get_protocol_name


@pytest.mark.parametrize(
    "protocol_name",
    ["zkLend", "Nostra Alpha", "Nostra Mainnet"]
)
def test_protocol_names(protocol_name):
    """Test that protocol name is correctly returned"""
    mock_state = MockState()
    mock_state.PROTOCOL_NAME = protocol_name
    assert mock_state.get_protocol_name == protocol_name


def test_get_protocol_helper():
    """Test the get_protocol helper function"""
    from dashboard_app.helpers.loans_table import get_protocol
    
    mock_state = MockState()
    mock_state.PROTOCOL_NAME = "Test Protocol"
    assert get_protocol(mock_state) == "Test Protocol"
    