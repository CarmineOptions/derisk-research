"""
Tests for zklend state
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from decimal import Decimal
from data_handler.handlers.loan_states.zklend.events import (
    ZkLendState
    )

class TestZkLendState(unittest.TestCase):

    def setUp(self):
        """Set up the ZkLendState instance and mock dependencies."""
        self.verbose_user = "user_123"
        self.zk_lend_state = ZkLendState(verbose_user=self.verbose_user)
        self.zk_lend_state.db_connector = MagicMock()
        
        # Mock loan entity and interest rate model structures
        self.zk_lend_state.loan_entities = {
            self.verbose_user: MagicMock(),
            "user_456": MagicMock()
        }
        self.zk_lend_state.interest_rate_models = MagicMock()
        self.zk_lend_state.interest_rate_models.collateral = {"TOKEN": Decimal("1.1")}
        self.zk_lend_state.interest_rate_models.debt = {"TOKEN": Decimal("0.9")}

    @patch("ZklendDataParser.parse_accumulators_sync_event")
    def test_process_accumulators_sync_event(self, mock_parse):
        """Test that process_accumulators_sync_event updates the correct interest rates."""
        mock_parse.return_value = MagicMock(
            token="TOKEN", lending_accumulator=Decimal("1.1"), debt_accumulator=Decimal("0.9")
        )
        event_data = pd.Series({"data": "mock_data"})
        
        self.zk_lend_state.process_accumulators_sync_event(event_data)
        
        self.assertEqual(self.zk_lend_state.interest_rate_models.collateral["TOKEN"], Decimal("1.1"))
        self.assertEqual(self.zk_lend_state.interest_rate_models.debt["TOKEN"], Decimal("0.9"))

    @patch("ZklendDataParser.parse_deposit_event")
    def test_process_deposit_event(self, mock_parse):
        """Test that process_deposit_event correctly updates user deposits and collateral."""
        mock_parse.return_value = MagicMock(user=self.verbose_user, token="TOKEN", face_amount=Decimal("110"))
        event_data = pd.Series({"data": "mock_data", "block_number": 1001, "timestamp": 163827})
        self.zk_lend_state.loan_entities[self.verbose_user].deposit.increase_value = MagicMock()
        self.zk_lend_state.loan_entities[self.verbose_user].collateral.increase_value = MagicMock()
        
        self.zk_lend_state.process_deposit_event(event_data)

        raw_amount = Decimal("110") / Decimal("1.1")
        self.zk_lend_state.loan_entities[self.verbose_user].deposit.increase_value.assert_called_once_with(
            token="TOKEN", value=raw_amount
        )
        self.zk_lend_state.loan_entities[self.verbose_user].extra_info.block = 1001
        self.zk_lend_state.loan_entities[self.verbose_user].extra_info.timestamp = 163827

    @patch("ZklendDataParser.parse_collateral_enabled_event")
    def test_process_collateral_enabled_event(self, mock_parse):
        """Test that process_collateral_enabled_event enables collateral for the correct token."""
        mock_parse.return_value = MagicMock(user=self.verbose_user, token="TOKEN")
        event_data = pd.Series({"data": "mock_data", "block_number": 1002, "timestamp": 163828})
        self.zk_lend_state.loan_entities[self.verbose_user].collateral_enabled = {}
        
        self.zk_lend_state.process_collateral_enabled_event(event_data)
        
        self.assertTrue(self.zk_lend_state.loan_entities[self.verbose_user].collateral_enabled["TOKEN"])
        self.zk_lend_state.db_connector.save_collateral_enabled_by_user.assert_called_once()

    @patch("ZklendDataParser.parse_withdrawal_event")
    def test_process_withdrawal_event(self, mock_parse):
        """Test that process_withdrawal_event correctly decreases deposit and collateral values."""
        mock_parse.return_value = MagicMock(user=self.verbose_user, token="TOKEN", face_amount=Decimal("55"))
        event_data = pd.Series({"data": "mock_data", "block_number": 1003, "timestamp": 163829})
        self.zk_lend_state.loan_entities[self.verbose_user].deposit.increase_value = MagicMock()
        self.zk_lend_state.loan_entities[self.verbose_user].collateral.increase_value = MagicMock()
        
        self.zk_lend_state.process_withdrawal_event(event_data)
        
        raw_amount = Decimal("55") / Decimal("1.1")
        self.zk_lend_state.loan_entities[self.verbose_user].deposit.increase_value.assert_any_call(
            token="TOKEN", value=-raw_amount
        )
        self.zk_lend_state.loan_entities[self.verbose_user].collateral.increase_value.assert_any_call(
            token="TOKEN", value=-raw_amount
        )

    @patch("ZklendDataParser.parse_borrowing_event")
    def test_process_borrowing_event(self, mock_parse):
        """Test that process_borrowing_event increases the user's debt by the borrowed amount."""
        mock_parse.return_value = MagicMock(user=self.verbose_user, token="TOKEN", raw_amount=Decimal("200"))
        event_data = pd.Series({"data": "mock_data", "block_number": 1004, "timestamp": 163830})
        
        self.zk_lend_state.process_borrowing_event(event_data)
        
        self.zk_lend_state.loan_entities[self.verbose_user].debt.increase_value.assert_called_once_with(
            token="TOKEN", value=Decimal("200")
        )

    @patch("ZklendDataParser.parse_repayment_event")
    def test_process_repayment_event(self, mock_parse):
        """Test that process_repayment_event decreases the user's debt by the repaid amount."""
        mock_parse.return_value = MagicMock(beneficiary=self.verbose_user, token="TOKEN", raw_amount=Decimal("100"))
        event_data = pd.Series({"data": "mock_data", "block_number": 1005, "timestamp": 163831})
        
        self.zk_lend_state.process_repayment_event(event_data)
        
        self.zk_lend_state.loan_entities[self.verbose_user].debt.increase_value.assert_called_once_with(
            token="TOKEN", value=-Decimal("100")
        )

    @patch("ZklendDataParser.parse_liquidation_event")
    def test_process_liquidation_event(self, mock_parse):
        """Test that process_liquidation_event updates debt and collateral during liquidation."""
        mock_parse.return_value = MagicMock(
            user=self.verbose_user,
            debt_token="DEBT_TOKEN",
            debt_raw_amount=Decimal("150"),
            collateral_token="COLLATERAL_TOKEN",
            collateral_amount=Decimal("60")
        )
        event_data = pd.Series({"data": "mock_data", "block_number": 1006, "timestamp": 163832})
        self.zk_lend_state.loan_entities[self.verbose_user].debt.increase_value = MagicMock()
        self.zk_lend_state.loan_entities[self.verbose_user].collateral.increase_value = MagicMock()
        
        self.zk_lend_state.process_liquidation_event(event_data)

        collateral_raw_amount = Decimal("60") / Decimal("1.1")
        self.zk_lend_state.loan_entities[self.verbose_user].debt.increase_value.assert_any_call(
            token="DEBT_TOKEN", value=-Decimal("150")
        )
        self.zk_lend_state.loan_entities[self.verbose_user].collateral.increase_value.assert_any_call(
            token="COLLATERAL_TOKEN", value=-collateral_raw_amount
        )