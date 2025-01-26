"""Test module for ZkLendState."""
import decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data_handler.handlers.loan_states.zklend.events import ZkLendState
from shared.custom_types import Portfolio, ZkLendCollateralEnabled


@pytest.fixture
def mock_db_connector():
    """Create a mocked database connector"""
    connector = MagicMock()
    connector.write_loan_states_to_db = MagicMock()
    connector.save_collateral_enabled_by_user = MagicMock()

    connector.engine = MagicMock()
    connector.engine.begin = MagicMock()
    connector.engine.begin.return_value._enter_ = MagicMock()
    connector.engine.begin.return_value._exit_ = MagicMock()

    return connector


@pytest.fixture
def mock_portfolio():
    """Creates a mock portfolio"""
    portfolio = MagicMock(spec=Portfolio)
    portfolio.increase_value = MagicMock()
    portfolio.set_value = MagicMock()
    portfolio._getitem_ = MagicMock(return_value=decimal.Decimal("1.0"))
    return portfolio


@pytest.fixture
def zklend_state(mock_db_connector):
    """Create a ZkLendState instance with mocked dependencies."""
    with patch(
        "data_handler.handlers.loan_states.zklend.events.InitializerDBConnector"
    ) as mock_db_class, patch("sqlalchemy.orm.declarative_base") as mock_base:

        mock_metadata = MagicMock()
        mock_metadata.create_all = MagicMock()
        mock_base_instance = MagicMock()
        mock_base_instance.metadata = mock_metadata
        mock_base.return_value = mock_base_instance

        mock_db_class.return_value = mock_db_connector
        mock_db_connector.engine = MagicMock()

        state = ZkLendState()
        state.interest_rate_models = MagicMock()
        state.interest_rate_models.collateral = {
            "0x123": decimal.Decimal("1.1"),
            "0x456": decimal.Decimal("1.05"),
            "0x789": decimal.Decimal("1.2"),  
        }
        state.interest_rate_models.debt = {
            "0x123": decimal.Decimal("1.2"),
            "0x456": decimal.Decimal("1.15"),
            "0x789": decimal.Decimal("1.3"),
        }
        return state


@pytest.fixture
def sample_event():
    return pd.Series(
        {"block_number": 12345, "timestamp": 1234567890, "data": ["0x123", "0x456", int(1e18)]}
    )


class TestZkLendState:
    def test_init(self, zklend_state):
        """Test ZkLendState initialization"""
        assert hasattr(zklend_state, "loan_entities")
        assert hasattr(zklend_state, "db_connector")
        assert isinstance(zklend_state.loan_entities, dict)

    def test_process_deposit_event(self, zklend_state, sample_event, mock_portfolio):
        """Test deposit event processing"""
        mock_parsed_data = MagicMock()
        mock_parsed_data.user = "0x123"
        mock_parsed_data.token = "0x456"
        mock_parsed_data.face_amount = int(1e18)

        with patch(
            "data_handler.handler_tools.data_parser.zklend.ZklendDataParser.parse_deposit_event",
            return_value=mock_parsed_data,
        ):
            user = mock_parsed_data.user
            loan_entity = MagicMock()
            loan_entity.deposit = mock_portfolio
            loan_entity.collateral = mock_portfolio
            loan_entity.collateral_enabled = ZkLendCollateralEnabled()
            loan_entity.collateral_enabled.get = MagicMock(return_value=False)
            loan_entity.extra_info = MagicMock()

            zklend_state.loan_entities[user] = loan_entity

            zklend_state.process_deposit_event(sample_event)

            mock_portfolio.increase_value.assert_called_once_with(
                token=mock_parsed_data.token,
                value=mock_parsed_data.face_amount
                / zklend_state.interest_rate_models.collateral[mock_parsed_data.token],
            )
            assert loan_entity.extra_info.block == 12345
            assert loan_entity.extra_info.timestamp == 1234567890

    def test_process_withdrawal_event(self, zklend_state, sample_event, mock_portfolio):
        """Test withdrawal event processing"""
        mock_parsed_data = MagicMock()
        mock_parsed_data.user = "0x123"
        mock_parsed_data.token = "0x456"
        mock_parsed_data.amount = int(1e18)

        with patch(
            "data_handler.handlers.loan_states.zklend.events.ZklendDataParser.parse_withdrawal_event",
            return_value=mock_parsed_data,
        ):
            user = mock_parsed_data.user
            loan_entity = MagicMock()
            loan_entity.deposit = mock_portfolio
            loan_entity.collateral = mock_portfolio
            loan_entity.collateral_enabled = ZkLendCollateralEnabled()
            loan_entity.collateral_enabled.get = MagicMock(return_value=True)
            loan_entity.extra_info = MagicMock()

            zklend_state.loan_entities[user] = loan_entity
            zklend_state.process_withdrawal_event(sample_event)

            mock_portfolio.increase_value.assert_called()
            assert loan_entity.extra_info.block == 12345
            assert loan_entity.extra_info.timestamp == 1234567890

    def test_process_borrowing_event(self, zklend_state, sample_event, mock_portfolio):
        """Test borrowing event processing"""
        mock_parsed_data = MagicMock()
        mock_parsed_data.user = "0x123"
        mock_parsed_data.token = "0x456"
        mock_parsed_data.raw_amount = decimal.Decimal("1.0")

        with patch(
            "data_handler.handler_tools.data_parser.zklend.ZklendDataParser.parse_borrowing_event",
            return_value=mock_parsed_data,
        ):
            user = mock_parsed_data.user
            loan_entity = MagicMock()
            loan_entity.debt = mock_portfolio
            loan_entity.extra_info = MagicMock()

            zklend_state.loan_entities[user] = loan_entity

            zklend_state.process_borrowing_event(sample_event)

            mock_portfolio.increase_value.assert_called_once_with(
                token=mock_parsed_data.token, value=mock_parsed_data.raw_amount
            )
            assert loan_entity.extra_info.block == 12345
            assert loan_entity.extra_info.timestamp == 1234567890

    def test_process_liquidation_event(self, zklend_state, sample_event, mock_portfolio):
        """Test liquidation event processing"""
        mock_parsed_data = MagicMock()
        mock_parsed_data.user = "0x123"
        mock_parsed_data.debt_token = "0x456"
        mock_parsed_data.debt_raw_amount = decimal.Decimal("1.0")
        mock_parsed_data.collateral_token = "0x789"
        mock_parsed_data.collateral_amount = int(1e18)

        with patch(
            "data_handler.handler_tools.data_parser.zklend.ZklendDataParser.parse_liquidation_event",
            return_value=mock_parsed_data,
        ):
            user = mock_parsed_data.user
            loan_entity = MagicMock()
            loan_entity.debt = mock_portfolio
            loan_entity.deposit = mock_portfolio
            loan_entity.collateral = mock_portfolio
            loan_entity.collateral_enabled = ZkLendCollateralEnabled()
            loan_entity.collateral_enabled._getitem_ = MagicMock(return_value=True)
            loan_entity.extra_info = MagicMock()

            zklend_state.loan_entities[user] = loan_entity

            zklend_state.process_liquidation_event(sample_event)

            mock_portfolio.increase_value.assert_called()
            assert loan_entity.extra_info.block == 12345
            assert loan_entity.extra_info.timestamp == 1234567890
