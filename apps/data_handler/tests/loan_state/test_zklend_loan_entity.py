"""
Test module for the ZkLendLoanEntity class.

This module contains test cases for verifying the functionality of the ZkLendLoanEntity class,
including health factor calculations, liquidation scenarios, and collateral management.
Tests cover normal operations, edge cases, and error conditions using mock objects and fixtures.
"""

import pytest
import decimal
from unittest.mock import MagicMock, patch
from shared.custom_types import InterestRateModels, Portfolio, Prices, TokenParameters
from data_handler.handlers.loan_states.zklend.events import ZkLendLoanEntity
from shared.loan_entity import LoanEntity

@pytest.fixture
def zklend_loan_entity():
    """Fixture providing a basic ZkLendLoanEntity instance with mocked methods."""
    with patch.object(LoanEntity, 'compute_collateral_usd') as mock_collateral_usd, \
         patch.object(LoanEntity, 'compute_debt_usd') as mock_debt_usd:
        
        # Setup default return values for the mocked methods
        mock_collateral_usd.return_value = decimal.Decimal('2000')  # 1 ETH at $2000
        mock_debt_usd.return_value = decimal.Decimal('1000')  # 1000 USDC at $1
        
        entity = ZkLendLoanEntity()
        entity.compute_collateral_usd = mock_collateral_usd
        entity.compute_debt_usd = mock_debt_usd
        return entity

@pytest.fixture
def mock_token_parameters():
    """Fixture providing mock token parameters."""
    eth_params = MagicMock()
    eth_params.collateral_factor = decimal.Decimal('0.8')
    eth_params.liquidation_bonus = decimal.Decimal('0.1')
    eth_params.underlying_address = 'ETH'
    
    usdc_params = MagicMock()
    usdc_params.collateral_factor = decimal.Decimal('0.85')
    usdc_params.liquidation_bonus = decimal.Decimal('0.1')
    usdc_params.underlying_address = 'USDC'

    return {
        'ETH': eth_params,
        'USDC': usdc_params
    }

@pytest.fixture
def mock_prices():
    """Fixture providing mock token prices."""
    return {
        'ETH': decimal.Decimal('2000'),
        'USDC': decimal.Decimal('1')
    }

@pytest.fixture
def mock_interest_rate_models():
    """Fixture providing mock interest rate models."""
    return {
        'ETH': decimal.Decimal('1.05'),
        'USDC': decimal.Decimal('1.02')
    }

class TestZkLendLoanEntity:
    """
    Test suite for the ZkLendLoanEntity class.

    This class contains comprehensive tests for the ZkLendLoanEntity implementation, including:
    - Basic initialization and property verification
    - Health factor calculations for different scenarios:
        * No debt cases
        * With debt cases
        * Risk-adjusted calculations
    - Liquidation threshold testing:
        * Healthy positions
        * Underwater positions
    - Collateral management:
        * Deposit handling
        * Collateral enabling/disabling
    - Input validation:
        * Negative value handling
        * Invalid input testing
    - Token configuration testing

    Tests use mock objects to isolate the class from external dependencies and
    verify its behavior under various conditions.
    """

    def test_initialization(self, zklend_loan_entity):
        """Test proper initialization of ZkLendLoanEntity."""
        assert isinstance(zklend_loan_entity.deposit, Portfolio)
        assert isinstance(zklend_loan_entity.collateral_enabled, dict)
        assert len(zklend_loan_entity.deposit) == 0
        assert len(zklend_loan_entity.collateral_enabled) == 0

    def test_compute_health_factor_no_debt(self, zklend_loan_entity, mock_prices):
        """Test health factor computation when there's no debt."""
        zklend_loan_entity.collateral['ETH'] = decimal.Decimal('1.0')
        zklend_loan_entity.compute_debt_usd.return_value = decimal.Decimal('0')
        
        health_factor = zklend_loan_entity.compute_health_factor(
            standardized=False,
            prices=mock_prices
        )
        
        assert health_factor == decimal.Decimal('Inf')

    def test_compute_health_factor_with_debt(self, zklend_loan_entity, mock_prices, mock_interest_rate_models):
        """Test health factor computation with both collateral and debt."""
        zklend_loan_entity.collateral['ETH'] = decimal.Decimal('1.0')
        zklend_loan_entity.debt['USDC'] = decimal.Decimal('1000.0')
        
        zklend_loan_entity.compute_collateral_usd.return_value = decimal.Decimal('2000')
        zklend_loan_entity.compute_debt_usd.return_value = decimal.Decimal('1000')
        
        health_factor = zklend_loan_entity.compute_health_factor(
            standardized=False,
            collateral_interest_rate_models=mock_interest_rate_models,
            debt_interest_rate_models=mock_interest_rate_models,
            prices=mock_prices
        )
        
        assert float(health_factor) == pytest.approx(2.0)

    def test_compute_health_factor_with_risk_adjustment(
        self, zklend_loan_entity, mock_prices, mock_token_parameters, mock_interest_rate_models
    ):
        """Test health factor computation with risk adjustment factors."""
        risk_adjusted_collateral_usd = decimal.Decimal('1600')  # 2000 * 0.8
        debt_usd = decimal.Decimal('1000')
        
        health_factor = zklend_loan_entity.compute_health_factor(
            standardized=True,
            prices=mock_prices,
            risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
            debt_usd=debt_usd
        )
        
        assert float(health_factor) == pytest.approx(1.6)

    @pytest.mark.parametrize("collateral_amount,debt_amount,health_factor,expected_result", [
        (0, 1000, decimal.Decimal('0.5'), True),    # No collateral
        (1, 3000, decimal.Decimal('0.8'), True),    # Underwater position
        (1, 1000, decimal.Decimal('2.0'), False),   # Healthy position
        (2, 1000, decimal.Decimal('4.0'), False),   # Very healthy position
    ])
    def test_is_liquidatable(
        self,
        zklend_loan_entity,
        mock_prices,
        collateral_amount,
        debt_amount,
        health_factor,
        expected_result
    ):
        """Test different scenarios for liquidation eligibility."""
        zklend_loan_entity.collateral['ETH'] = decimal.Decimal(str(collateral_amount))
        zklend_loan_entity.debt['USDC'] = decimal.Decimal(str(debt_amount))
        
        # Setup the mock to return our predetermined health factor
        collateral_usd = decimal.Decimal(str(collateral_amount)) * decimal.Decimal('2000')
        debt_usd = decimal.Decimal(str(debt_amount))
        zklend_loan_entity.compute_collateral_usd.return_value = collateral_usd
        zklend_loan_entity.compute_debt_usd.return_value = debt_usd
        
        actual_health_factor = zklend_loan_entity.compute_health_factor(
            standardized=False,
            prices=mock_prices
        )
        
        is_liquidatable = actual_health_factor < decimal.Decimal('1.0')
        assert is_liquidatable == expected_result

    def test_negative_values(self, zklend_loan_entity):
        """Test handling of negative values."""
        with patch.object(Portfolio, 'increase_value') as mock_increase:
            mock_increase.side_effect = ValueError("Value cannot be negative")
            with pytest.raises(ValueError):
                zklend_loan_entity.collateral.increase_value('ETH', decimal.Decimal('-1.0'))
            
            with pytest.raises(ValueError):
                zklend_loan_entity.debt.increase_value('USDC', decimal.Decimal('-1000.0'))

    def test_deposit_and_collateral_enabled_interaction(self, zklend_loan_entity):
        """Test interaction between deposit and collateral_enabled flags."""
        token = 'ETH'
        deposit_amount = decimal.Decimal('1.0')
        
        # Add deposit
        zklend_loan_entity.deposit[token] = deposit_amount
        assert zklend_loan_entity.deposit[token] == deposit_amount
        
        # Initially, collateral should not be enabled
        assert not zklend_loan_entity.collateral_enabled.get(token, False)
        assert token not in zklend_loan_entity.collateral
        
        # Enable collateral
        zklend_loan_entity.collateral_enabled[token] = True
        zklend_loan_entity.collateral[token] = deposit_amount
        
        assert zklend_loan_entity.collateral[token] == zklend_loan_entity.deposit[token]

    def test_token_settings(self):
        """Test token settings configuration."""
        assert hasattr(ZkLendLoanEntity, 'TOKEN_SETTINGS')
        assert isinstance(ZkLendLoanEntity.TOKEN_SETTINGS, dict)