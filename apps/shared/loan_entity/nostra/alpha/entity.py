"""
Event processing for Nostra Alpha protocol, including loan and collateral management.
"""

import decimal
from shared.loan_entity.nostra.alpha.settings import NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
from shared.custom_types import InterestRateModels, Portfolio, Prices, TokenParameters
from shared.loan_entity import LoanEntity

LIQUIDATION_HEALTH_FACTOR_THRESHOLD = decimal.Decimal("1")
TARGET_HEALTH_FACTOR = decimal.Decimal("1.25")


class NostraAlphaLoanEntity(LoanEntity):
    """
    A class that describes the Nostra
    Alpha loan entity. On top of the abstract `LoanEntity`, it implements the
    `non_interest_bearing_collateral`
    and `interest_bearing_collateral` attributes in order to help with accounting for
    the changes in collateral.
    This is because Nostra Alpha allows the user to decide the amount of collateral that
    earns interest and the amount that doesn't. We keep all balances in raw amounts.
    """

    TOKEN_SETTINGS = NOSTRA_ALPHA_SPECIFIC_TOKEN_SETTINGS
    # TODO: Move these to `PROTOCOL_SETTINGS` (similar to `TOKEN_SETTINGS`)? Might be useful when
    # `compute_health_factor` is generalized.
    LIQUIDATION_HEALTH_FACTOR_THRESHOLD = LIQUIDATION_HEALTH_FACTOR_THRESHOLD
    TARGET_HEALTH_FACTOR = TARGET_HEALTH_FACTOR

    def __init__(self) -> None:
        super().__init__()
        self.non_interest_bearing_collateral: Portfolio = Portfolio()
        self.interest_bearing_collateral: Portfolio = Portfolio()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_token_parameters: TokenParameters | None = None,
        collateral_interest_rate_model: InterestRateModels | None = None,
        debt_token_parameters: TokenParameters | None = None,
        debt_interest_rate_model: InterestRateModels | None = None,
        prices: Prices | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        risk_adjusted_debt_usd: float | None = None,
    ) -> float:
        """
        Computes the health factor of the loan entity.
        :param standardized: If True, the health factor is standardized.
        :param collateral_token_parameters: Collateral token parameters.
        :param collateral_interest_rate_model: Collateral interest rate model.
        :param debt_token_parameters: Debt token parameters.
        :param debt_interest_rate_model: Debt interest rate model.
        :param prices: Prices of the tokens.
        :param risk_adjusted_collateral_usd: Risk-adjusted collateral in USD.
        :param risk_adjusted_debt_usd: Risk-adjusted debt in USD.
        :return: Health factor.
        """
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_token_parameters=collateral_token_parameters,
                collateral_interest_rate_model=collateral_interest_rate_model,
                prices=prices,
            )
        if risk_adjusted_debt_usd is None:
            risk_adjusted_debt_usd = self.compute_debt_usd(
                risk_adjusted=True,
                collateral_token_parameters=debt_token_parameters,
                debt_interest_rate_model=debt_interest_rate_model,
                prices=prices,
            )

        if risk_adjusted_debt_usd == 0.0:
            # TODO: Assumes collateral is positive.
            return float("inf")
        return risk_adjusted_collateral_usd / risk_adjusted_debt_usd

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_addresses: list[str],
        collateral_token_parameters: TokenParameters,
        health_factor: float,
        debt_token_parameters: TokenParameters,
        debt_token_addresses: list[str],
        debt_token_debt_amount: decimal.Decimal,
        debt_token_price: float,
    ) -> float:
        """
        Computes the amount of debt to be liquidated.
        :param collateral_token_addresses: Collateral token addresses.
        :param collateral_token_parameters: Collateral token parameters.
        :param health_factor: Health factor.
        :param debt_token_parameters: Debt token parameters.
        :param debt_token_addresses: Debt token addresses.
        :param debt_token_debt_amount: Debt token debt amount.
        :param debt_token_price: Debt token price.
        :return:
        """
        # TODO: figure out what to do when there's multiple debt token addresses
        liquidator_fee_usd = 0.0
        liquidation_amount_usd = 0.0
        # TODO: do we need such a complicated way to compute this?
        # Choose the most optimal collateral_token to be liquidated.
        for collateral_token_address in collateral_token_addresses:
            # TODO: Commit a PDF with the derivation of the formula?
            # See an example of a liquidation here:
            # https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
            liquidator_fee = min(
                collateral_token_parameters[
                    collateral_token_address
                ].liquidator_fee_beta
                * (self.LIQUIDATION_HEALTH_FACTOR_THRESHOLD - health_factor),
                collateral_token_parameters[
                    collateral_token_address
                ].liquidator_fee_max,
            )
            total_fee = (
                liquidator_fee
                + collateral_token_parameters[collateral_token_address].protocol_fee
            )
            max_liquidation_percentage = (self.TARGET_HEALTH_FACTOR - health_factor) / (
                self.TARGET_HEALTH_FACTOR
                - (
                    collateral_token_parameters[
                        collateral_token_address
                    ].collateral_factor
                    * debt_token_parameters[debt_token_addresses[0]].debt_factor
                    * (1.0 + total_fee)
                )
            )
            max_liquidation_percentage = min(max_liquidation_percentage, 1.0)
            max_liquidation_amount = max_liquidation_percentage * float(
                debt_token_debt_amount
            )
            max_liquidation_amount_usd = (
                debt_token_price
                * max_liquidation_amount
                / (10 ** debt_token_parameters[debt_token_addresses[0]].decimals)
            )
            max_liquidator_fee_usd = liquidator_fee * max_liquidation_amount_usd
            if max_liquidator_fee_usd > liquidator_fee_usd:
                liquidator_fee_usd = max_liquidator_fee_usd
                liquidation_amount_usd = max_liquidation_amount_usd
        return liquidation_amount_usd
