from abc import ABC
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from shared.types import Portfolio, TokenValues
from .settings import TOKEN_SETTINGS as BASE_TOKEN_SETTINGS
from .settings import TokenSettings as BaseTokenSettings


@dataclass
class SpecificTokenSettings:
    collateral_factor: Decimal
    debt_factor: Decimal


@dataclass
class TokenSettings(SpecificTokenSettings, BaseTokenSettings):
    pass


LOAN_ENTITY_SPECIFIC_TOKEN_SETTINGS: dict[str, SpecificTokenSettings] = {
    "ETH": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "wBTC": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "USDC": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "DAI": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "USDT": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "wstETH": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "LORDS": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
    "STRK": SpecificTokenSettings(
        collateral_factor=Decimal("1"), debt_factor=Decimal("1")
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=BASE_TOKEN_SETTINGS[token].symbol,
        decimal_factor=BASE_TOKEN_SETTINGS[token].decimal_factor,
        address=BASE_TOKEN_SETTINGS[token].address,
        collateral_factor=LOAN_ENTITY_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=LOAN_ENTITY_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
    )
    for token in BASE_TOKEN_SETTINGS
}


class InterestRateModels(TokenValues):
    """
    A class that describes the state of the interest rate indices which help transform face amounts into raw amounts.
    Raw amount is the amount that would have been accumulated into the face amount if it were deposited at genesis.
    """

    def __init__(self) -> None:
        super().__init__(init_value=Decimal("1"))


class LoanEntity(ABC):
    """
    A class that describes and entity which can hold collateral, borrow debt and be liquidable. For example, on
    Starknet, such an entity is the user in case of zkLend, Nostra Alpha and Nostra Mainnet, or an individual loan in
    case od Hashstack V0 and Hashstack V1.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self) -> None:
        self.collateral: Portfolio = Portfolio()
        self.debt: Portfolio = Portfolio()

    def compute_collateral_usd(
        self,
        risk_adjusted: bool,
        collateral_interest_rate_models: InterestRateModels,
        prices: TokenValues,
    ) -> Decimal:
        """
        Compute's collateral usd of interest
        :param risk_adjusted: bool
        :param collateral_interest_rate_models: InterestRateModels
        :param prices: TokenValues
        :return: Decimal
        """
        return sum(
            token_amount
            / self.TOKEN_SETTINGS[token].decimal_factor
            * (
                self.TOKEN_SETTINGS[token].collateral_factor
                if risk_adjusted
                else Decimal("1")
            )
            * collateral_interest_rate_models.values[token]
            * prices.values[token]
            for token, token_amount in self.collateral.values.items()
        )

    def compute_debt_usd(
        self,
        risk_adjusted: bool,
        debt_interest_rate_models: InterestRateModels,
        prices: TokenValues,
    ) -> Decimal:
        """
        Compute's debt usd of interest
        :param risk_adjusted: bool
        :param debt_interest_rate_models: InterestRateModels
        :param prices: TokenValues
        :return: Decimal
        """
        return sum(
            token_amount
            / self.TOKEN_SETTINGS[token].decimal_factor
            / (
                self.TOKEN_SETTINGS[token].debt_factor
                if risk_adjusted
                else Decimal("1")
            )
            * debt_interest_rate_models.values[token]
            * prices.values[token]
            for token, token_amount in self.debt.values.items()
        )


class State(ABC):
    """
    A class that describes the state of all loan entities of the given lending protocol.
    """

    EVENTS_METHODS_MAPPING: dict[str, str] = {}

    def __init__(
        self,
        loan_entity_class: LoanEntity,
        verbose_user: str | None = None,
    ) -> None:
        self.loan_entity_class: LoanEntity = loan_entity_class
        self.verbose_user: str | None = verbose_user
        self.loan_entities: defaultdict = defaultdict(self.loan_entity_class)
        self.collateral_interest_rate_models: InterestRateModels = InterestRateModels()
        self.debt_interest_rate_models: InterestRateModels = InterestRateModels()
        self.last_block_number: int = 0
