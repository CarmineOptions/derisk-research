import abc
import asyncio
import collections
import dataclasses
import decimal
from typing import Optional

import pandas
from error_handler import BOT
from error_handler.values import MessageTemplates
from handler_tools.types import (CollateralAndDebtInterestRateModels,
                                 CollateralAndDebtTokenParameters,
                                 InterestRateModels, Portfolio, Prices,
                                 TokenParameters, TokenValues)
from handlers.exceptions import TokenSettingsNotFound
from handlers.helpers import ExtraInfo
from handlers.settings import TOKEN_SETTINGS, TokenSettings


@dataclasses.dataclass
class NostraAlphaSpecificTokenSettings(TokenSettings):
    # TODO: Load these via chain calls?
    # Source: Starkscan, e.g.
    # https://starkscan.co/call/0x06f619127a63ddb5328807e535e56baa1e244c8923a3b50c123d41dcbed315da_1_1 for ETH.
    collateral_factor: decimal.Decimal
    # TODO: Add source.
    debt_factor: decimal.Decimal
    # TODO: Add sources for liquidation parameters.
    liquidator_fee_beta: decimal.Decimal
    liquidator_fee_max: decimal.Decimal
    protocol_fee: decimal.Decimal
    protocol_token_address: str


NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS: dict[str, NostraAlphaSpecificTokenSettings] = {
    "ETH": NostraAlphaSpecificTokenSettings(
        symbol="ETH",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        collateral_factor=decimal.Decimal("0.8"),
        debt_factor=decimal.Decimal("0.9"),
        liquidator_fee_beta=decimal.Decimal("2.75"),
        liquidator_fee_max=decimal.Decimal("0.25"),
        protocol_fee=decimal.Decimal("0.02"),
        protocol_token_address="0x04f89253e37ca0ab7190b2e9565808f105585c9cacca6b2fa6145553fa061a41",
    ),
    "wBTC": NostraAlphaSpecificTokenSettings(
        symbol="wBTC",
        decimal_factor=decimal.Decimal("1e8"),
        address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        collateral_factor=decimal.Decimal("0.7"),
        debt_factor=decimal.Decimal("0.8"),
        liquidator_fee_beta=decimal.Decimal("2.75"),
        liquidator_fee_max=decimal.Decimal("0.25"),
        protocol_fee=decimal.Decimal("0.02"),
        protocol_token_address="0x07788bc687f203b6451f2a82e842b27f39c7cae697dace12edfb86c9b1c12f3d",
    ),
    "USDC": NostraAlphaSpecificTokenSettings(
        symbol="USDC",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        collateral_factor=decimal.Decimal("0.9"),
        debt_factor=decimal.Decimal("0.95"),
        liquidator_fee_beta=decimal.Decimal("1.65"),
        liquidator_fee_max=decimal.Decimal("0.15"),
        protocol_fee=decimal.Decimal("0.02"),
        protocol_token_address="0x05327df4c669cb9be5c1e2cf79e121edef43c1416fac884559cd94fcb7e6e232",
    ),
    "DAI": NostraAlphaSpecificTokenSettings(
        symbol="DAI",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        collateral_factor=decimal.Decimal("0.8"),
        debt_factor=decimal.Decimal("0.95"),
        liquidator_fee_beta=decimal.Decimal("2.2"),
        liquidator_fee_max=decimal.Decimal("0.2"),
        protocol_fee=decimal.Decimal("0.02"),
        protocol_token_address="0x02ea39ba7a05f0c936b7468d8bc8d0e1f2116916064e7e163e7c1044d95bd135",
    ),
    "USDT": NostraAlphaSpecificTokenSettings(
        symbol="USDT",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
        collateral_factor=decimal.Decimal("0.8"),
        debt_factor=decimal.Decimal("0.95"),
        liquidator_fee_beta=decimal.Decimal("1.65"),
        liquidator_fee_max=decimal.Decimal("0.15"),
        protocol_fee=decimal.Decimal("0.02"),
        protocol_token_address="0x040375d0720245bc0d123aa35dc1c93d14a78f64456eff75f63757d99a0e6a83",
    ),
    # TODO: These (`wstETH`,  `LORDS`, and `STRK`) are actually Nostra Mainnet tokens.
    "wstETH": NostraAlphaSpecificTokenSettings(
        symbol="wstETH",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",
        collateral_factor=decimal.Decimal("0.8"),
        debt_factor=decimal.Decimal("0.9"),
        liquidator_fee_beta=decimal.Decimal("999999"),
        liquidator_fee_max=decimal.Decimal("0.25"),
        protocol_fee=decimal.Decimal("0.02"),
        protocol_token_address="",
    ),
    "LORDS": NostraAlphaSpecificTokenSettings(
        symbol="LORDS",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",
        collateral_factor=decimal.Decimal("1"),  # TODO: Not observed yet.
        debt_factor=decimal.Decimal("0.8"),
        liquidator_fee_beta=decimal.Decimal("1"),  # TODO: Not observed yet.
        liquidator_fee_max=decimal.Decimal("0"),  # TODO: Not observed yet.
        protocol_fee=decimal.Decimal("0"),  # TODO: Not observed yet.
        protocol_token_address="",
    ),
    "STRK": NostraAlphaSpecificTokenSettings(
        symbol="STRK",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
        collateral_factor=decimal.Decimal("0.6"),
        debt_factor=decimal.Decimal("0.8"),
        liquidator_fee_beta=decimal.Decimal("999999"),  # TODO: updated?
        liquidator_fee_max=decimal.Decimal("0.35"),  # TODO: updated?
        protocol_fee=decimal.Decimal("0.02"),  # TODO: updated?
        protocol_token_address="",
    ),
}


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
            collateral_token_parameters: TokenParameters,
            collateral_interest_rate_model: InterestRateModels,
            prices: Prices,
    ) -> float:
        """
        Compute the value of the collateral in USD.
        :param risk_adjusted: risk adjusted
        :param collateral_token_parameters: token parameters for collateral
        :param collateral_interest_rate_model: token parameters for interest rate model
        :param prices: Prices
        :return: sum of the value of the collateral in USD
        """
        return sum(
            float(token_amount)
            / (10 ** collateral_token_parameters[token].decimals)
            * (collateral_token_parameters[token].collateral_factor if risk_adjusted else 1.0)
            * float(collateral_interest_rate_model[token])
            * prices[collateral_token_parameters[token].underlying_address]
            for token, token_amount in self.collateral.items()
        )

    def compute_debt_usd(
        self,
        risk_adjusted: bool,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
        prices: TokenValues,
    ) -> decimal.Decimal:
        return sum(
            float(token_amount)
            / (10 ** debt_token_parameters[token].decimals)
            / (debt_token_parameters[token].debt_factor if risk_adjusted else 1.0)
            * float(debt_interest_rate_model[token])
            * prices[debt_token_parameters[token].underlying_address]
            for token, token_amount in self.debt.items()
        )

    @abc.abstractmethod
    def compute_health_factor(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def compute_debt_to_be_liquidated(self, *args, **kwargs):
        pass

    def get_collateral_str(
        self,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels,
    ) -> str:
        return ", ".join(
            f"{token}: {round(token_amount / (10 ** collateral_token_parameters[token].decimals) * collateral_interest_rate_model[token], 4)}"
            for token, token_amount in self.collateral.items()
            if token_amount > decimal.Decimal("0")
        )

    def get_debt_str(
        self,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
    ) -> str:
        return ", ".join(
            f"{token}: {round(token_amount / (10 ** debt_token_parameters[token].decimals) * debt_interest_rate_model[token], 4)}"
            for token, token_amount in self.debt.items()
            if token_amount > decimal.Decimal("0")
        )

    def has_collateral(self) -> bool:
        return any(token_amount for token_amount in self.collateral.values())

    def has_debt(self) -> bool:
        return any(token_amount for token_amount in self.debt.values())


class State(abc.ABC):
    """
    A class that describes the state of all loan entities of the given lending protocol.
    """

    PROTOCOL_NAME: str = None
    ADDRESSES_TO_TOKENS: dict[str, str] = {}
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
        self.interest_rate_models: CollateralAndDebtInterestRateModels = (
            CollateralAndDebtInterestRateModels()
        )
        # These models reflect the interest rates at which users borrow funds.
        self.debt_interest_rate_models: InterestRateModels = InterestRateModels()
        self.token_parameters: CollateralAndDebtTokenParameters = (
            CollateralAndDebtTokenParameters()
        )
        self.last_block_number: int = 0
        self.last_interest_rate_block_number: int = 0

    def process_event(self, method_name: str, event: pandas.Series) -> None:
        # TODO: Save the timestamp of each update?
        if event["block_number"] >= self.last_block_number:
            self.last_block_number = event["block_number"]
            method = getattr(self, method_name, "")
            if method:
                method(event)

    @abc.abstractmethod
    def compute_liquidable_debt_at_price(self, *args, **kwargs):
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

    def get_token_name(self, address: str) -> str | None:
        """
        Get the token name from the address.
        :param address: str
        :return: str | None
        """
        # FIXME Remove Address to token mapping while doing refactoring for Nostra
        try:
            token_name = self.ADDRESSES_TO_TOKENS[address]
        except KeyError:
            asyncio.run(
                BOT.send_message(
                    message=MessageTemplates.NEW_TOKEN_MESSAGE.format(
                        protocol_name=self.PROTOCOL_NAME, address=address
                    )
                )
            )
            raise TokenSettingsNotFound(address=address, protocol=self.PROTOCOL_NAME)

        return token_name
