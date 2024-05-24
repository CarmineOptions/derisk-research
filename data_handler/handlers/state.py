import abc
import collections
import dataclasses
import decimal
from typing import Optional

import pandas

from data_handler.handlers.helpers import Portfolio, TokenValues, ExtraInfo
from data_handler.handlers.settings import TOKEN_SETTINGS, TokenSettings


@dataclasses.dataclass
class SpecificTokenSettings:
    collateral_factor: decimal.Decimal
    debt_factor: decimal.Decimal


@dataclasses.dataclass
class TokenSettings(SpecificTokenSettings, TokenSettings):
    pass


LOAN_ENTITY_SPECIFIC_TOKEN_SETTINGS: dict[str, SpecificTokenSettings] = {
    "ETH": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "wBTC": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDC": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "DAI": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDT": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "wstETH": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "LORDS": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "STRK": SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=TOKEN_SETTINGS[token].symbol,
        decimal_factor=TOKEN_SETTINGS[token].decimal_factor,
        address=TOKEN_SETTINGS[token].address,
        collateral_factor=LOAN_ENTITY_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=LOAN_ENTITY_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
    )
    for token in TOKEN_SETTINGS
}


class InterestRateModels(TokenValues):
    """
    A class that describes the state of the interest rate indices which help transform face amounts into raw amounts.
    Raw amount is the amount that would have been accumulated into the face amount if it were deposited at genesis.
    """

    def __init__(self) -> None:
        super().__init__(init_value=decimal.Decimal("1"))


class LoanEntity(abc.ABC):
    """
    A class that describes and entity which can hold collateral, borrow debt and be liquidable. For example, on
    Starknet, such an entity is the user in case of zkLend, Nostra Alpha and Nostra Mainnet, or an individual loan in
    case od Hashstack V0 and Hashstack V1.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self) -> None:
        self.collateral: Portfolio = Portfolio()
        self.debt: Portfolio = Portfolio()
        self.extra_info: ExtraInfo = ExtraInfo()

    def compute_collateral_usd(
        self,
        risk_adjusted: bool,
        collateral_interest_rate_models: InterestRateModels,
        prices: TokenValues,
    ) -> decimal.Decimal:
        return sum(
            token_amount
            / self.TOKEN_SETTINGS[token].decimal_factor
            * (
                self.TOKEN_SETTINGS[token].collateral_factor
                if risk_adjusted
                else decimal.Decimal("1")
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
    ) -> decimal.Decimal:
        return sum(
            token_amount
            / self.TOKEN_SETTINGS[token].decimal_factor
            / (
                self.TOKEN_SETTINGS[token].debt_factor
                if risk_adjusted
                else decimal.Decimal("1")
            )
            * debt_interest_rate_models.values[token]
            * prices.values[token]
            for token, token_amount in self.debt.values.items()
        )

    @abc.abstractmethod
    def compute_health_factor(self):
        pass

    @abc.abstractmethod
    def compute_debt_to_be_liquidated(self):
        pass

    def get_collateral_str(
        self, collateral_interest_rate_models: InterestRateModels
    ) -> str:
        return ", ".join(
            f"{token}: {round(token_amount / self.TOKEN_SETTINGS[token].decimal_factor * collateral_interest_rate_models.values[token], 4)}"
            for token, token_amount in self.collateral.values.items()
            if token_amount > decimal.Decimal("0")
        )

    def get_debt_str(self, debt_interest_rate_models: InterestRateModels) -> str:
        return ", ".join(
            f"{token}: {round(token_amount / self.TOKEN_SETTINGS[token].decimal_factor * debt_interest_rate_models.values[token], 4)}"
            for token, token_amount in self.debt.values.items()
            if token_amount > decimal.Decimal("0")
        )

    def has_collateral(self) -> bool:
        if any(token_amount for token_amount in self.collateral.values.values()):
            return True
        return False

    def has_debt(self) -> bool:
        if any(token_amount for token_amount in self.debt.values.values()):
            return True
        return False


class State(abc.ABC):
    """
    A class that describes the state of all loan entities of the given lending protocol.
    """

    EVENTS_METHODS_MAPPING: dict[str, str] = {}

    def __init__(
        self,
        loan_entity_class: LoanEntity,
        verbose_user: Optional[str] = None,
    ) -> None:
        self.loan_entity_class: LoanEntity = loan_entity_class
        self.verbose_user: Optional[str] = verbose_user
        self.loan_entities: collections.defaultdict = collections.defaultdict(
            self.loan_entity_class
        )
        # These models reflect the interest rates at which users lend/stake funds.
        self.collateral_interest_rate_models: InterestRateModels = InterestRateModels()
        # These models reflect the interest rates at which users borrow funds.
        self.debt_interest_rate_models: InterestRateModels = InterestRateModels()
        self.last_block_number: int = 0

    def process_event(self, method_name: str, event: pandas.Series) -> None:
        # TODO: Save the timestamp of each update?
        if event["block_number"] >= self.last_block_number:
            self.last_block_number = event["block_number"]
            method = getattr(self, method_name, "")
            if method:
                method(event)

    @abc.abstractmethod
    def compute_liquidable_debt_at_price(self):
        pass

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def compute_number_of_active_loan_entities(self) -> int:
        return sum(
            loan_entity.has_collateral() or loan_entity.has_debt()
            for loan_entity in self.loan_entities.values()
        )

    # TODO: This method will likely differ across protocols. -> Leave undefined?
    def compute_number_of_active_loan_entities_with_debt(self) -> int:
        return sum(
            loan_entity.has_debt() for loan_entity in self.loan_entities.values()
        )
