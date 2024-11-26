import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from datetime import datetime

from data_handler.handlers.health_ratio_level.health_ratio_handlers import BaseHealthRatioHandler
from shared.state import State, LoanEntity
from shared.types import TokenValues
from shared.constants import ProtocolIDs

class MockState(State):
    """Mock State class for testing"""
    pass

class MockLoanEntity(LoanEntity):
    """Mock LoanEntity class for testing"""
    pass

@pytest.fixture
def mock_loan_data():
    """Fixture for sample loan data"""
    return [
        MagicMock(
            user="user1",
            debt={"ETH": Decimal("1.5")},
            collateral={"USDC": Decimal("3000")}
        ),
        MagicMock(
            user="user2",
            debt={"ETH": Decimal("2.0")},
            collateral={"USDC": Decimal("4000")}
        )
    ]

@pytest.fixture
def mock_interest_rates():
    """Fixture for sample interest rate data"""
    return MagicMock(
        collateral={"USDC": Decimal("0.05")},
        debt={"ETH": Decimal("0.08")}
    )

class TestBaseHealthRatioHandler:
    
    @pytest.fixture
    def handler(self):
        """Create a BaseHealthRatioHandler instance for testing"""
        return BaseHealthRatioHandler(
            state_class=MockState,
            loan_entity_class=MockLoanEntity
        )

    def test_initialization(self, handler):
        """Test proper initialization of BaseHealthRatioHandler"""
        assert isinstance(handler, BaseHealthRatioHandler)
        assert handler.state_class == MockState
        assert handler.loan_entity_class == MockLoanEntity
        assert handler.db_connector is not None

    def test_fetch_data(self, handler, mock_db_connector, mock_loan_data, mock_interest_rates):
        """Test fetch_data method"""
        handler.db_connector = mock_db_connector
        mock_db_connector.get_latest_block_loans.return_value = mock_loan_data
        mock_db_connector.get_last_interest_rate_record_by_protocol_id.return_value = mock_interest_rates

        loan_states, interest_rates = handler.fetch_data(ProtocolIDs.ZKLEND)
        
        assert loan_states == mock_loan_data
        assert interest_rates == mock_interest_rates
        mock_db_connector.get_latest_block_loans.assert_called_once()
        mock_db_connector.get_last_interest_rate_record_by_protocol_id.assert_called_once_with(
            protocol_id=ProtocolIDs.ZKLEND
        )

    def test_initialize_loan_entities(self, handler, mock_loan_data):
        """Test initialize_loan_entities method"""
        state = MockState()
        result_state = handler.initialize_loan_entities(state, mock_loan_data)

        assert len(result_state.loan_entities) == 2
        assert "user1" in result_state.loan_entities
        assert "user2" in result_state.loan_entities
        
        # Verify loan entity data
        user1_entity = result_state.loan_entities["user1"]
        assert isinstance(user1_entity, MockLoanEntity)
        assert isinstance(user1_entity.debt, TokenValues)
        assert isinstance(user1_entity.collateral, TokenValues)
        assert user1_entity.debt.values["ETH"] == Decimal("1.5")
        assert user1_entity.collateral.values["USDC"] == Decimal("3000")

    @pytest.mark.parametrize("health_ratio,expected", [
        (Decimal("1.5"), True),
        (Decimal("0.8"), True),
        (Decimal("0"), False),
        (Decimal("-1"), False),
        (Decimal("Infinity"), False)
    ])
    def test_health_ratio_is_valid(self, handler, health_ratio, expected):
        """Test health_ratio_is_valid method with various inputs"""
        assert handler.health_ratio_is_valid(health_ratio) == expected

    def test_fetch_data_handles_db_error(self, handler, mock_db_connector):
        """Test fetch_data error handling"""
        handler.db_connector = mock_db_connector
        mock_db_connector.get_latest_block_loans.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            handler.fetch_data(ProtocolIDs.ZKLEND)
        assert "Database error" in str(exc_info.value)

    def test_initialize_loan_entities_with_empty_data(self, handler):
        """Test initialize_loan_entities with empty data"""
        state = MockState()
        result_state = handler.initialize_loan_entities(state, [])
        assert len(result_state.loan_entities) == 0

    def test_initialize_loan_entities_maintains_existing_state(self, handler, mock_loan_data):
        """Test that initialize_loan_entities preserves existing state data"""
        state = MockState()
        # Add some pre-existing data
        existing_entity = MockLoanEntity()
        existing_entity.debt = TokenValues(values={"BTC": Decimal("1.0")})
        existing_entity.collateral = TokenValues(values={"ETH": Decimal("10.0")})
        state.loan_entities["existing_user"] = existing_entity

        result_state = handler.initialize_loan_entities(state, mock_loan_data)
        
        # Check that new data was added
        assert len(result_state.loan_entities) == 3
        # Verify existing data remains
        assert "existing_user" in result_state.loan_entities
        assert result_state.loan_entities["existing_user"].debt.values["BTC"] == Decimal("1.0")