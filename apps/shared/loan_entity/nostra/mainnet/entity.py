import logging
from ..alpha import NostraAlphaLoanEntity
from shared.constants import ProtocolIDs
from shared.custom_types import InterestRateModels, Prices, TokenParameters

logger = logging.getLogger(__name__)


class NostraMainnetLoanEntity(NostraAlphaLoanEntity):
    """
    A class that describes the state of all Nostra Mainnet loan entities.
      All methods for correct processing of every
    relevant event are implemented in `.nostra_alpha.NostraAlphaState`.
    """

    PROTOCOL_NAME = ProtocolIDs.NOSTRA_MAINNET.value
    # TODO: fetch from chain
    TARGET_HEALTH_FACTOR = 1.25
    # TODO: confirm this
    # Source: https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
    LIQUIDATION_BONUS = 0.2

    def compute_debt_to_be_liquidated(
        self,
        collateral_token_addresses: list[str],
        debt_token_addresses: list[str],
        prices: Prices,
        collateral_token_parameters: TokenParameters,
        debt_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels | None = None,
        debt_interest_rate_model: InterestRateModels | None = None,
        risk_adjusted_collateral_usd: float | None = None,
        risk_adjusted_debt_usd: float | None = None,
    ) -> float:
        """
        Computes the amount of debt that can be liquidated given the
        current state of the loan entity.
        :param collateral_token_addresses: Collateral token addresses.
        :param debt_token_addresses:  Debt token addresses.
        :param prices: Prices of all tokens.
        :param collateral_token_parameters: Collateral token parameters.
        :param debt_token_parameters: Debt token parameters.
        :param collateral_interest_rate_model: Collateral interest rate model.
        :param debt_interest_rate_model: Debt interest rate model.
        :param risk_adjusted_collateral_usd: Risk-adjusted collateral value in USD.
        :param risk_adjusted_debt_usd: Risk-adjusted debt value in USD.
        :return: float
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

        # TODO: Commit a PDF with the derivation of the formula?
        # See an example of a liquidation here:
        # https://docs.nostra.finance/lend/liquidations/an-example-of-liquidation.
        numerator = (
            risk_adjusted_collateral_usd
            - risk_adjusted_debt_usd * self.TARGET_HEALTH_FACTOR
        )
        # TODO: figure out what to do when there's multiple collateral token addresses
        collateral_token_address = collateral_token_addresses[0]
        # TODO: figure out what to do when there's multiple collateral token addresses
        debt_token_address = debt_token_addresses[0]
        denominator = (
            collateral_token_parameters[collateral_token_address].collateral_factor
            * (1 + self.LIQUIDATION_BONUS)
            - (1 / debt_token_parameters[debt_token_address].debt_factor)
            * self.TARGET_HEALTH_FACTOR
        )
        max_debt_to_be_liquidated = numerator / denominator
        # The liquidator can't liquidate more debt than what is available.
        debt_to_be_liquidated = min(
            float(self.debt[debt_token_address]), max_debt_to_be_liquidated
        )
        return debt_to_be_liquidated
