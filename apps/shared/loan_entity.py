from abc import ABC, abstractmethod
from decimal import Decimal

from shared.constants import TOKEN_SETTINGS
from shared.types import (
    ExtraInfo,
    InterestRateModels,
    Portfolio,
    Prices,
    TokenParameters,
    TokenSettings,
    TokenValues,
)


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
        self.extra_info: ExtraInfo = ExtraInfo

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
            * (
                collateral_token_parameters[token].collateral_factor
                if risk_adjusted
                else 1.0
            )
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
    ) -> Decimal:
        """
        Compute the value of the debt in USD.
        :param risk_adjusted: risk adjusted
        :param debt_token_parameters: token parameters for debt
        :param debt_interest_rate_model: token parameters for interest rate model
        :param prices: Prices
        :return: Decimal
        """
        return sum(
            float(token_amount)
            / (10 ** debt_token_parameters[token].decimals)
            / (debt_token_parameters[token].debt_factor if risk_adjusted else 1.0)
            * float(debt_interest_rate_model[token])
            * prices[debt_token_parameters[token].underlying_address]
            for token, token_amount in self.debt.items()
        )

    @abstractmethod
    def compute_health_factor(self, *args, **kwargs):
        pass

    @abstractmethod
    def compute_debt_to_be_liquidated(self, *args, **kwargs):
        pass

    def get_collateral_str(
        self,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels,
    ) -> str:
        """
        Get a string representation of the collateral.
        :param collateral_token_parameters:
        :param collateral_interest_rate_model:
        :return: string representation of the collateral.
        """
        return ", ".join(
            f"{token}: {round(token_amount / (10 ** collateral_token_parameters[token].decimals) * collateral_interest_rate_model[token], 4)}"
            for token, token_amount in self.collateral.items()
            if token_amount > Decimal("0")
        )

    def get_debt_str(
        self,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
    ) -> str:
        """
        Get a string representation of the debt.
        :param debt_token_parameters:
        :param debt_interest_rate_model:
        :return: string representation of the debt.
        """
        return ", ".join(
            f"{token}: {round(token_amount / (10 ** debt_token_parameters[token].decimals) * debt_interest_rate_model[token], 4)}"
            for token, token_amount in self.debt.items()
            if token_amount > Decimal("0")
        )

    def has_collateral(self) -> bool:
        """
        Check if the entity has any collateral.
        :return: bool
        """
        try:
            collateral_tokens = self.collateral.values()
        except TypeError:
            collateral_tokens = self.collateral.values

        return any(token_amount for token_amount in collateral_tokens)

    def has_debt(self) -> bool:
        """
        Check if the entity has any debt.
        :return: bool
        """
        return any(token_amount for token_amount in self.debt.values)
