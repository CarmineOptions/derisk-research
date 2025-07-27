"""
zkLend Event Handlers

This module handles events for zkLend loan entities, tracking deposits,
borrowings, repayments, collateral status, and liquidations.

Classes:
    - ZkLendLoanEntity: Manages deposit and collateral status for loans.
    - ZkLendState: Processes events and computes liquidatable debt.

Functions:
    - collect_token_parameters: Fetches token parameters.
    - process_*_event: Updates loan states based on events.
"""

import decimal
import logging
from decimal import Decimal
from typing import Optional

from shared.loan_entity.zklend.settings import ZKLEND_SPECIFIC_TOKEN_SETTINGS
from shared.loan_entity import LoanEntity


from shared.custom_types import (
    InterestRateModels,
    Portfolio,
    Prices,
    TokenParameters,
    TokenValues,
    ZkLendCollateralEnabled,
)

logger = logging.getLogger(__name__)

ZKLEND_MARKET: str = (
    "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"
)
EVENTS_METHODS_MAPPING: dict[str, str] = {
    "AccumulatorsSync": "process_accumulators_sync_event",
    "zklend::market::Market::AccumulatorsSync": "process_accumulators_sync_event",
    "Deposit": "process_deposit_event",
    "zklend::market::Market::Deposit": "process_deposit_event",
    "CollateralEnabled": "process_collateral_enabled_event",
    "zklend::market::Market::CollateralEnabled": "process_collateral_enabled_event",
    "CollateralDisabled": "process_collateral_disabled_event",
    "zklend::market::Market::CollateralDisabled": "process_collateral_disabled_event",
    "Withdrawal": "process_withdrawal_event",
    "zklend::market::Market::Withdrawal": "process_withdrawal_event",
    "Borrowing": "process_borrowing_event",
    "zklend::market::Market::Borrowing": "process_borrowing_event",
    "Repayment": "process_repayment_event",
    "zklend::market::Market::Repayment": "process_repayment_event",
    "Liquidation": "process_liquidation_event",
    "zklend::market::Market::Liquidation": "process_liquidation_event",
}

# ZKLEND_SPECIFIC_TOKEN_SETTINGS = asyncio.run(fetch_zklend_specific_token_settings())


class ZkLendLoanEntity(LoanEntity):
    """
    A class that describes the zkLend loan entity. On top of the abstract `LoanEntity`,
    it implements the `deposit` and
    `collateral_enabled` attributes in order to help with accounting for the changes in
    collateral. This is because
    under zkLend, collateral is the amount deposited that is specifically flagged with
      `collateral_enabled` set to True
    for the given token. To properly account for the changes in collateral, we must hold the
    information about the
    given token's deposits being enabled as collateral or not and the amount of the deposits.
    We keep all balances in raw
    amounts.
    """

    TOKEN_SETTINGS = ZKLEND_SPECIFIC_TOKEN_SETTINGS

    def __init__(self) -> None:
        super().__init__()
        self.deposit: Portfolio = Portfolio()
        self.collateral_enabled: ZkLendCollateralEnabled = ZkLendCollateralEnabled()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_models: Optional[InterestRateModels] = None,
        debt_interest_rate_models: Optional[InterestRateModels] = None,
        prices: Optional[TokenValues] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_model=collateral_interest_rate_models,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_model=debt_interest_rate_models,
                prices=prices,
            )

        if debt_usd == decimal.Decimal("0"):
            return decimal.Decimal("Inf")

        return Decimal(risk_adjusted_collateral_usd) / debt_usd

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_underlying_address: str,
        debt_token_underlying_address: str,
        prices: Prices,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: Optional[InterestRateModels] = None,
        debt_token_parameters: TokenParameters | None = None,
        debt_interest_rate_model: Optional[InterestRateModels] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_model=collateral_interest_rate_model,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_model=debt_interest_rate_model,
                prices=prices,
            )

        # TODO: Commit a PDF with the derivation of the formula?
        numerator = debt_usd - risk_adjusted_collateral_usd
        denominator = prices[debt_token_underlying_address] * (
            1
            - collateral_token_parameters[
                collateral_token_underlying_address
            ].collateral_factor
            * (
                1
                + collateral_token_parameters[
                    collateral_token_underlying_address
                ].liquidation_bonus
            )
        )
        max_debt_to_be_liquidated = numerator / Decimal(str(denominator))
        # The liquidator can't liquidate more debt than what is available.
        debt_to_be_liquidated = min(
            float(self.debt.values[debt_token_underlying_address]),
            max_debt_to_be_liquidated,
        )
        return debt_to_be_liquidated
