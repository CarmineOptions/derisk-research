from shared.types import ZkLendCollateralEnabled, Portfolio, InterestRateModels, TokenParameters, Prices, LoanEntity

class ZkLendLoanEntity(LoanEntity):
    """
    A class that describes the zkLend loan entity. On top of the abstract `LoanEntity`, it implements the `deposit` and
    `collateral_enabled` attributes in order to help with accounting for the changes in collateral. This is because
    under zkLend, collateral is the amount deposited that is specificaly flagged with `collateral_enabled` set to True
    for the given token. To properly account for the changes in collateral, we must hold the information about the
    given token's deposits being enabled as collateral or not and the amount of the deposits. We keep all balances in raw
    amounts.
    """

    def __init__(self) -> None:
        super().__init__()
        self.deposit: Portfolio = Portfolio()
        self.collateral_enabled: ZkLendCollateralEnabled = ZkLendCollateralEnabled()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_token_parameters: TokenParameters | None = None,
        collateral_interest_rate_model: InterestRateModels | None = None,
        debt_token_parameters: TokenParameters | None = None,
        debt_interest_rate_model: InterestRateModels | None = None,
        prices: Prices | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        debt_usd: float | None = None,
    ) -> float:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_token_parameters=collateral_token_parameters,
                collateral_interest_rate_model=collateral_interest_rate_model,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                collateral_token_parameters=debt_token_parameters,
                debt_interest_rate_model=debt_interest_rate_model,
                prices=prices,
            )

        if standardized:
            # Denominator is the value of (risk-adjusted) collateral at which the loan entity can be liquidated.
            # TODO: denominator = debt_usd * liquidation_threshold??
            denominator = debt_usd
        else:
            denominator = debt_usd

        if denominator == 0.0:
            # TODO: Assumes collateral is positive.
            return float("inf")
        return risk_adjusted_collateral_usd / denominator

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_underlying_address: str,
        debt_token_underlying_address: str,
        prices: Prices,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels | None = None,
        debt_token_parameters: TokenParameters | None = None,
        debt_interest_rate_model: InterestRateModels | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        debt_usd: float | None = None,
    ) -> float:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_collateral_usd(
                risk_adjusted=True,
                collateral_token_parameters=collateral_token_parameters,
                collateral_interest_rate_model=collateral_interest_rate_model,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                collateral_token_parameters=debt_token_parameters,
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
        max_debt_to_be_liquidated = numerator / denominator
        # The liquidator can't liquidate more debt than what is available.
        debt_to_be_liquidated = min(
            float(self.debt[debt_token_underlying_address]), max_debt_to_be_liquidated
        )
        return debt_to_be_liquidated