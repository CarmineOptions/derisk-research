import copy
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import pandas as pd

from .helpers import Portfolio, TokenValues, get_symbol
from .settings import TOKEN_SETTINGS as BASE_TOKEN_SETTINGS
from .settings import TokenSettings as BaseTokenSettings
from .state import InterestRateModels, LoanEntity, State

ADDRESS: str = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"


@dataclass
class ZkLendSpecificTokenSettings:
    collateral_factor: Decimal
    debt_factor: Decimal
    liquidation_bonus: Decimal
    protocol_token_address: str


@dataclass
class TokenSettings(ZkLendSpecificTokenSettings, BaseTokenSettings):
    pass


ZKLEND_SPECIFIC_TOKEN_SETTINGS: dict[str, ZkLendSpecificTokenSettings] = {
    "ETH": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.80"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.10"),
        protocol_token_address="0x01b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1",
    ),
    "wBTC": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.70"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.15"),
        protocol_token_address="0x02b9ea3acdb23da566cee8e8beae3125a1458e720dea68c4a9a7a2d8eb5bbb4a",
    ),
    "USDC": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.80"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.10"),
        protocol_token_address="0x047ad51726d891f972e74e4ad858a261b43869f7126ce7436ee0b2529a98f486",
    ),
    "DAI": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.70"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.10"),
        protocol_token_address="0x062fa7afe1ca2992f8d8015385a279f49fad36299754fb1e9866f4f052289376",
    ),
    "USDT": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.80"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.10"),
        protocol_token_address="0x00811d8da5dc8a2206ea7fd0b28627c2d77280a515126e62baa4d78e22714c4a",
    ),
    "wstETH": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.80"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.10"),
        protocol_token_address="0x0536aa7e01ecc0235ca3e29da7b5ad5b12cb881e29034d87a4290edbb20b7c28",
    ),
    "LORDS": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("1"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0"),
        protocol_token_address="",
    ),
    "STRK": ZkLendSpecificTokenSettings(
        collateral_factor=Decimal("0.50"),
        debt_factor=Decimal("1"),
        liquidation_bonus=Decimal("0.15"),
        protocol_token_address="0x06d8fa671ef84f791b7f601fa79fea8f6ceb70b5fa84189e3159d532162efc21",
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=BASE_TOKEN_SETTINGS[token].symbol,
        decimal_factor=BASE_TOKEN_SETTINGS[token].decimal_factor,
        address=BASE_TOKEN_SETTINGS[token].address,
        collateral_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
        liquidation_bonus=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].liquidation_bonus,
        protocol_token_address=ZKLEND_SPECIFIC_TOKEN_SETTINGS[
            token
        ].protocol_token_address,
    )
    for token in BASE_TOKEN_SETTINGS
}

# Keys are values of the "key_name" column in the database, values are the respective method names.
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


class ZkLendLoanEntity(LoanEntity):
    """
    A class that describes the zkLend loan entity. On top of the abstract `LoanEntity`, it implements the `deposit` and
    `collateral_enabled` attributes in order to help with accounting for the changes in collateral. This is because
    under zkLend, collateral is the amount deposited that is specificaly flagged with `collateral_enabled` set to True
    for the given token. To properly account for the changes in collateral, we must hold the information about the
    given token's deposits being enabled as collateral or not and the amount of the deposits. We keep all balances in raw
    amounts.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self) -> None:
        super().__init__()
        self.deposit: Portfolio = Portfolio()
        self.collateral_enabled: TokenValues = TokenValues(init_value=False)

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_models: InterestRateModels | None = None,
        debt_interest_rate_models: InterestRateModels | None = None,
        prices: TokenValues | None = TokenValues(),
        risk_adjusted_collateral_usd: Decimal | None = None,
        debt_usd: Decimal | None = None,
    ) -> Decimal:
        """
        Compute's health ratio factor for zkLend loans.
        :param standardized: InterestRateModels | None = None
        :param collateral_interest_rate_models: InterestRateModels | None = None
        :param debt_interest_rate_models: InterestRateModels | None = None
        :param prices: TokenValues | None = None
        :param risk_adjusted_collateral_usd: Decimal | None = None
        :param debt_usd: Decimal | None = None
        :return: Decimal
        """
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                collateral_interest_rate_models=collateral_interest_rate_models,
                prices=prices,
                risk_adjusted=True,
            )

        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
                risk_adjusted=False,
            )

        if debt_usd == Decimal("0"):
            return Decimal("Inf")

        return risk_adjusted_collateral_usd / debt_usd


class ZkLendState(State):
    """
    A class that describes the state of all zkLend loan entities. It implements methods for correct processing of every
    relevant event.
    """

    EVENTS_METHODS_MAPPING: dict[str, str] = EVENTS_METHODS_MAPPING

    def __init__(
        self,
        verbose_user: str | None = None,
    ) -> None:
        super().__init__(
            loan_entity_class=ZkLendLoanEntity,
            verbose_user=verbose_user,
        )
