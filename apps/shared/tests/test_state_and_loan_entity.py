"""
Test module for State and LoanEntity classes.
This module provides unit tests for the State and LoanEntity abstract base classes,
using mock implementations to test core functionality.
"""
import pytest
from decimal import Decimal
import pandas as pd
from unittest.mock import Mock, patch
from dataclasses import dataclass


@dataclass
class MockMessage:
    """
    Mock implementation of Message class for testing.
    Used to simulate message handling without actual messaging infrastructure.
    """
    text: str
    is_sent: bool


@dataclass
class MockMessageTemplates:
    """
    Mock implementation of MessageTemplates for testing.
    Provides template messages used in error handling and notifications.
    """
    ENTRY_MESSAGE: str = "Now you will receive notifications if any error occurs."
    RETRY_ENTRY_MESSAGE: str = "You have already registered for error notifications."
    NEW_TOKEN_MESSAGE: str = "{protocol_name} has a new token with address {address}."


class MockErrorHandlerBot:
    """
    Mock implementation of ErrorHandlerBot for testing.
    Simulates bot functionality without actual messaging capabilities.
    """
    def __init__(self, token=None):
        """Initialize mock bot with optional token."""
        self.token = token

    async def send_message(self, message: str) -> None:
        """Mock implementation of message sending."""
        pass

# Initialize mock objects
mock_bot = MockErrorHandlerBot()
mock_message_templates = MockMessageTemplates()

# Mock dependencies
with patch.dict(
    "sys.modules",
    {
        "aiogram": Mock(),
        "shared.error_handler.notifications": Mock(BOT=mock_bot),
        "shared.error_handler": Mock(
            BOT=mock_bot,
            MessageTemplates=mock_message_templates,
            TokenSettingsNotFound=Exception,
        ),
    },
):
    from shared.types.base import (
        Portfolio,
        ExtraInfo,
        TokenParameters,
        InterestRateModels,
        Prices,
    )
    from shared.loan_entity import LoanEntity
    from shared.state import State


class MockLoanEntity(LoanEntity):
    """
    Mock implementation of LoanEntity for testing.
    Provides concrete implementations of abstract methods for testing purposes.
    """
    def __init__(self) -> None:
        super().__init__()

    def compute_health_factor(self, *args, **kwargs):
        """Compute mock health factor."""
        return 1.5

    def compute_debt_to_be_liquidated(self, *args, **kwargs):
        """Compute mock debt to be liquidated."""
        return Decimal("100")

    def has_debt(self) -> bool:
        """
        Check if the loan entity has any debt.
        :return: bool
        """
        return any(self.debt.values())


class MockState(State):
    """
    Mock implementation of State for testing.
    Provides concrete implementations of abstract methods and test-specific attributes.
    """
    PROTOCOL_NAME = "MockProtocol"
    ADDRESSES_TO_TOKENS = {"0x123": "MOCK_TOKEN"}
    EVENTS_METHODS_MAPPING = {"deposit": "process_deposit"}

    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        return Decimal("1000")


def test_mock_loan_entity_initialization():
    """Test MockLoanEntity initialization"""
    entity = MockLoanEntity()
    assert isinstance(entity.collateral, Portfolio)
    assert isinstance(entity.debt, Portfolio)
    assert entity.extra_info == ExtraInfo


def test_mock_loan_entity_compute_health_factor():
    """Test compute_health_factor returns expected value"""
    entity = MockLoanEntity()
    assert entity.compute_health_factor() == 1.5


def test_mock_loan_entity_compute_debt_to_be_liquidated():
    """Test compute_debt_to_be_liquidated returns expected value"""
    entity = MockLoanEntity()
    assert entity.compute_debt_to_be_liquidated() == Decimal("100")


def test_mock_loan_entity_has_collateral():
    """Test has_collateral method"""
    entity = MockLoanEntity()
    assert not entity.has_collateral()
    entity.collateral["TOKEN1"] = Decimal("1000")
    assert entity.has_collateral()


def test_mock_loan_entity_has_debt():
    """Test has_debt method"""
    entity = MockLoanEntity()
    assert not entity.has_debt()
    entity.debt["TOKEN1"] = Decimal("1000")
    assert entity.has_debt()


def test_mock_state_initialization():
    """Test MockState initialization"""
    state = MockState(MockLoanEntity)
    assert state.PROTOCOL_NAME == "MockProtocol"
    assert state.ADDRESSES_TO_TOKENS == {"0x123": "MOCK_TOKEN"}
    assert state.EVENTS_METHODS_MAPPING == {"deposit": "process_deposit"}


def test_mock_state_get_token_name():
    """Test get_token_name method"""
    state = MockState(MockLoanEntity)
    assert state.get_token_name("0x123") == "MOCK_TOKEN"
    with pytest.raises(Exception):
        state.get_token_name("invalid_address")


def test_mock_state_process_event():
    """Test process_event method"""
    state = MockState(MockLoanEntity)
    event = pd.Series({"block_number": 100, "data": "test_data"})

    state.process_event("deposit", event)
    assert state.last_block_number == 100


def test_mock_state_compute_number_of_active_loan_entities():
    """Test computation of active loan entities"""
    state = MockState(MockLoanEntity)

    # Add some loan entities
    entity1 = MockLoanEntity()
    entity1.collateral["TOKEN1"] = Decimal("1000")
    state.loan_entities["user1"] = entity1

    entity2 = MockLoanEntity()
    state.loan_entities["user2"] = entity2

    assert state.compute_number_of_active_loan_entities() == 1
    assert state.compute_number_of_active_loan_entities_with_debt() == 0


def test_mock_loan_entity_compute_collateral_usd():
    """Test collateral USD computation"""
    entity = MockLoanEntity()
    entity.collateral["TOKEN1"] = Decimal("1000000000000000000")  # 1 token

    # Create collateral parameters
    collateral_params = TokenParameters()
    collateral_params["TOKEN1"].decimals = 18
    collateral_params["TOKEN1"].collateral_factor = float(0.8)
    collateral_params["TOKEN1"].underlying_address = "0x123"

    # Create interest rate model
    # Use float for interest rate to match implementation
    interest_model = InterestRateModels()
    interest_model["TOKEN1"] = float(1.1)

    # Create prices
    prices = Prices()
    prices["0x123"] = float(1000)

    value = entity.compute_collateral_usd(
        risk_adjusted=True,
        collateral_token_parameters=collateral_params,
        collateral_interest_rate_model=interest_model,
        prices=prices,
    )

    # Expected calculation:
    # 1 token * 0.8 (collateral factor) * 1.1 (interest) * 1000 (price)
    # = 1 * 0.8 * 1.1 * 1000 = 880.0
    assert value == pytest.approx(880.0)


def test_mock_state_invalid_event_method():
    """Test handling of invalid event method"""
    state = MockState(MockLoanEntity)
    event = pd.Series({"block_number": 100, "data": "test_data"})

    # Should not raise an error for non-existent method
    state.process_event("non_existent_method", event)
    assert state.last_block_number == 100


def test_mock_loan_entity_portfolio_operations():
    """Test Portfolio addition and value operations"""
    entity = MockLoanEntity()

    # Test adding collateral
    entity.collateral["TOKEN1"] = Decimal("1000")
    entity.collateral["TOKEN2"] = Decimal("2000")

    # Test portfolio addition
    new_portfolio = Portfolio()
    new_portfolio["TOKEN1"] = Decimal("500")
    new_portfolio["TOKEN3"] = Decimal("1500")

    combined = entity.collateral + new_portfolio
    assert combined["TOKEN1"] == Decimal("1500")
    assert combined["TOKEN2"] == Decimal("2000")
    assert combined["TOKEN3"] == Decimal("1500")
