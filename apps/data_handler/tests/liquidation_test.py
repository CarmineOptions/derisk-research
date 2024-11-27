"""
Test the debt handler
"""

import pytest
from data_handler.handlers.liquidable_debt.debt_handlers import BaseDBLiquidableDebtDataHandler
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from data_handler.tests.conftest import mock_db_connector
from data_handler.handlers.helpers import get_collateral_token_range, get_range
from shared.state import State
from shared.loan_entity import LoanEntity
from data_handler.db.models.loan_states import LoanState


class TestBaseDBLiquidableDebtDataHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Automatically set up a mocked DBConnector for the handler.
        """
        self.handler = BaseDBLiquidableDebtDataHandler
        self.handler.db_connector = mock_db_connector

    def test_available_protocols(self):
        """
        Test that AVAILABLE_PROTOCOLS contains all protocol names from LendingProtocolNames.
        """
        with patch("data_handler.handlers.liquidable_debt.values.LendingProtocolNames", ["Hashstack_v0", "Hashstack_v1", "Nostra_alpha", "Nostra_mainnet", "zkLend"]):
            assert BaseDBLiquidableDebtDataHandler.AVAILABLE_PROTOCOLS == ["Hashstack_v0", "Hashstack_v1", "Nostra_alpha", "Nostra_mainnet", "zkLend"]
    
    def test_get_prices_range_valid_token(self):
        """
        Test get_prices_range when the token is in the token pairs list.
        """
        with patch("data_handler.handlers.settings.TOKEN_PAIRS", {"ETH": ("USDC", "USDT", "DAI")}):
            with patch("data_handler.handlers.helpers.get_collateral_token_range"):
                result = self.handler.get_prices_range("ETH", Decimal("100"))
                print(result)
                assert result == get_collateral_token_range("ETH", Decimal("100"))

    def test_get_prices_range_invalid_token(self):
        """
        Test get_prices_range when the token is not in the token pairs list.
        """
        with patch("data_handler.handlers.settings.TOKEN_PAIRS", {"BTC": "ETH"}):
            with patch("data_handler.handlers.helpers.get_range"):
                result = self.handler.get_prices_range("LTC", Decimal("100"))
                print(result)
                assert result == get_range(Decimal("0"), Decimal("130"), Decimal("1"))

    def test_fetch_data(self):
        """
        Test fetch_data retrieves the correct loan data and interest rate models from the DB.
        """
        with patch("data_handler.db.crud.DBConnector") as MockDBConnector:
            protocol_name = "ProtocolA"

            # Mock DB return values
            mock_loans = [{"loan_id": 1, "amount": 100}]
            mock_interest_rates = [{"protocol_id": protocol_name, "rate": 5}]

            # Configure mocked methods
            mock_db_connector = MockDBConnector.return_value
            mock_db_connector.get_loans.return_value = mock_loans
            mock_db_connector.get_last_interest_rate_record_by_protocol_id.return_value = mock_interest_rates
            self.handler.db_connector = mock_db_connector

            # Call the method
            loan_data, interest_rate_models = self.handler.fetch_data(self=self.handler, protocol_name=protocol_name)

            # Assertions for returned data
            assert loan_data == mock_loans, "Loan data mismatch"
            assert interest_rate_models == mock_interest_rates, "Interest rate models mismatch"

            # Ensure DBConnector methods were called with correct arguments
            mock_db_connector.get_loans.assert_called_once_with(model=LoanState, protocol=protocol_name)
            mock_db_connector.get_last_interest_rate_record_by_protocol_id.assert_called_once_with(protocol_id=protocol_name)