"""Test the health ratio handlers"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from data_handler.handlers.health_ratio_level.health_ratio_handlers import (
    BaseHealthRatioHandler,
)
from shared.state import State, LoanEntity
from shared.custom_types import TokenValues
from shared.constants import ProtocolIDs


class MockState(State):
    """Mock State class for testing"""

    PROTOCOL_NAME: str = ProtocolIDs.ZKLEND.value

    def __init__(self):
        self.loan_entities = {}
        self.collateral_interest_rate_models = None
        self.debt_interest_rate_models = None
        self.interest_rate_models = MagicMock(collateral={}, debt={})

    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        """Mock implementation of abstract method"""
        return Decimal("100.0")


class MockLoanEntity(LoanEntity):
    """Mock LoanEntity class for testing"""

    def __init__(self):
        self.debt = None
        self.collateral = None

    def compute_collateral_usd(self, **kwargs):
        return Decimal("1000.0")

    def compute_debt_usd(self, **kwargs):
        return Decimal("500.0")

    def compute_health_factor(self, **kwargs):
        return Decimal("2.0")

    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        """Mock implementation of abstract method"""
        return Decimal("100.0")

    def compute_debt_to_be_liquidated(self, *args, **kwargs):
        """Mock implementation of abstract method"""
        return Decimal("50.0")


@pytest.fixture
def mock_loan_data():
    """Fixture for sample loan data"""
    return [
        MagicMock(
            user="user1",
            debt={"ETH": Decimal("1.5")},
            collateral={"USDC": Decimal("3000")},
        ),
        MagicMock(
            user="user2",
            debt={"ETH": Decimal("2.0")},
            collateral={"USDC": Decimal("4000")},
        ),
    ]


class TestBaseHealthRatioHandler:

    @pytest.fixture(autouse=True)
    def setup(self, mock_db_connector):
        """Setup test instance"""
        with patch(
            "data_handler.handlers.health_ratio_level.health_ratio_handlers.DBConnector"
        ) as mock_db:
            mock_db.return_value = mock_db_connector
            self.handler = BaseHealthRatioHandler(
                state_class=MockState, loan_entity_class=MockLoanEntity
            )
            self.handler.db_connector = mock_db_connector

    def test_fetch_data(self, mock_db_connector):
        """Test fetch_data method"""
        mock_db_connector.get_latest_block_loans.return_value = []
        mock_db_connector.get_last_interest_rate_record_by_protocol_id.return_value = (
            MagicMock(
                collateral={"USDC": Decimal("0.05")}, debt={"ETH": Decimal("0.08")}
            )
        )

        loan_states, interest_rates = self.handler.fetch_data(ProtocolIDs.ZKLEND)

        assert mock_db_connector.get_latest_block_loans.called
        assert mock_db_connector.get_last_interest_rate_record_by_protocol_id.called
        assert isinstance(interest_rates.collateral, dict)
        assert isinstance(interest_rates.debt, dict)

    def test_initialize_loan_entities(self, mock_loan_data):
        """Test initialize_loan_entities method"""
        state = MockState()
        result = self.handler.initialize_loan_entities(state, mock_loan_data)

        assert len(result.loan_entities) == 2
        assert "user1" in result.loan_entities
        assert "user2" in result.loan_entities

        user1_entity = result.loan_entities["user1"]
        assert isinstance(user1_entity.debt, TokenValues)
        assert isinstance(user1_entity.collateral, TokenValues)
        assert user1_entity.debt.values["ETH"] == Decimal("1.5")
        assert user1_entity.collateral.values["USDC"] == Decimal("3000")

    def test_initialize_loan_entities_with_empty_data(self):
        """Test initialize_loan_entities with empty data"""
        state = MockState()
        result = self.handler.initialize_loan_entities(state, [])
        assert len(result.loan_entities) == 0

    @pytest.mark.parametrize(
        "health_ratio,expected",
        [
            (Decimal("1.5"), True),
            (Decimal("0.8"), True),
            (Decimal("0"), False),
            (Decimal("-1"), False),
            (Decimal("Infinity"), False),
        ],
    )
    def test_health_ratio_is_valid(self, health_ratio, expected):
        """Test health_ratio_is_valid with various inputs"""
        assert self.handler.health_ratio_is_valid(health_ratio) == expected

    def test_fetch_data_handles_db_error(self, mock_db_connector):
        """Test fetch_data error handling"""
        mock_db_connector.get_latest_block_loans.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(Exception) as exc_info:
            self.handler.fetch_data(ProtocolIDs.ZKLEND)
        assert "Database error" in str(exc_info.value)

    def test_initialize_loan_entities_maintains_existing_state(self, mock_loan_data):
        """Test that initialize_loan_entities preserves existing state"""
        state = MockState()
        # Add pre-existing data
        existing_entity = MockLoanEntity()
        existing_entity.debt = TokenValues(values={"BTC": Decimal("1.0")})
        existing_entity.collateral = TokenValues(values={"ETH": Decimal("10.0")})
        state.loan_entities["existing_user"] = existing_entity

        result_state = self.handler.initialize_loan_entities(state, mock_loan_data)

        assert len(result_state.loan_entities) == 3
        assert "existing_user" in result_state.loan_entities
        assert result_state.loan_entities["existing_user"].debt.values[
            "BTC"
        ] == Decimal("1.0")
