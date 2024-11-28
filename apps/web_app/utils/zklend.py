from dataclasses import dataclass
from decimal import Decimal

from .helpers import Portfolio, TokenValues
from .settings import TOKEN_SETTINGS as BASE_TOKEN_SETTINGS
from .settings import TokenSettings as BaseTokenSettings
from .state import InterestRateModels, LoanEntity, State
from shared.constants import ProtocolIDs

# IT GIVES `ModuleNotFoundError` THAT'S WHY I COMMENTED OUT IT
# from data_handler.handlers.loan_states.zklend.fetch_zklend_specific_token_settings import ZKLEND_SPECIFIC_TOKEN_SETTINGS

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


# IT GIVES `ModuleNotFoundError` THAT'S WHY I COMMENTED OUT IT
# TOKEN_SETTINGS: dict[str, TokenSettings] = {
#     token: TokenSettings(
#         symbol=BASE_TOKEN_SETTINGS[token].symbol,
#         decimal_factor=BASE_TOKEN_SETTINGS[token].decimal_factor,
#         address=BASE_TOKEN_SETTINGS[token].address,
#         collateral_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
#         debt_factor=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
#         liquidation_bonus=ZKLEND_SPECIFIC_TOKEN_SETTINGS[token].liquidation_bonus,
#         protocol_token_address=ZKLEND_SPECIFIC_TOKEN_SETTINGS[
#             token
#         ].protocol_token_address,
#     )
#     for token in BASE_TOKEN_SETTINGS
# }

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

    TOKEN_SETTINGS: dict[str, TokenSettings] = ...

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

    PROTOCOL_NAME: str = ProtocolIDs.ZKLEND.value
    EVENTS_METHODS_MAPPING: dict[str, str] = EVENTS_METHODS_MAPPING

    def __init__(
        self,
        verbose_user: str | None = None,
    ) -> None:
        super().__init__(
            loan_entity_class=ZkLendLoanEntity,
            verbose_user=verbose_user,
        )
