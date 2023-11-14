from typing import Any, Dict, Optional
import collections
import copy
import decimal
import logging

import pandas

import src.constants



logging.basicConfig(level=logging.INFO)



class TokenAmounts:
    """
    A class that describes the holdings of collateral or debt of a loan entity.
    """

    # TODO: Find a better solution to fix the discrepancies.
    MAX_ROUNDING_ERRORS: Dict[str, decimal.Decimal] = {
        "ETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
        "wBTC": decimal.Decimal("1e2"),
        "USDC": decimal.Decimal("1e4"),
        "DAI": decimal.Decimal("1e16"),
        "USDT": decimal.Decimal("1e4"),
        "wstETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
    }

    def __init__(self) -> None:
        # TODO: Get a better source of a list of tokens then src.constants.TOKEN_DECIMAL_FACTORS
        self.token_amounts: Dict[str, decimal.Decimal] = {x: decimal.Decimal("0") for x in src.constants.TOKEN_DECIMAL_FACTORS}

    def round_small_amount_to_zero(self, token: str):
        if (
            -self.MAX_ROUNDING_ERRORS[token]
            < self.token_amounts[token]
            < self.MAX_ROUNDING_ERRORS[token]
        ):
            self.token_amounts[token] = decimal.Decimal("0")

    def increase_value(self, token: str, amount: decimal.Decimal):
        self.token_amounts[token] += amount
        self.round_small_amount_to_zero(token=token)

    def rewrite_value(self, token: str, amount: decimal.Decimal):
        self.token_amounts[token] = amount
        self.round_small_amount_to_zero(token=token)


class LoanEntity:
    """
    A class that describes and entity which can hold collateral, borrow debt and be liquidable. For example, on 
    Starknet, such an entity is the user in case of zkLend and Nostra, or an individual loan in case od Hashstack.
    """

    # TODO: Implement a dataclass for `COLLATERAL_FACTORS`?
    COLLATERAL_FACTORS: Dict[str, decimal.Decimal] = {}
    # TODO: Implement a dataclass for `LIQUIDATION_BONUSES`?
    LIQUIDATION_BONUSES: Dict[str, decimal.Decimal] = {}

    def __init__(self) -> None:
        self.collateral: TokenAmounts = TokenAmounts()
        self.debt: TokenAmounts = TokenAmounts()

    def compute_collateral_usd(self, prices: Dict[str, decimal.Decimal]) -> decimal.Decimal:
        return sum(
            token_amount
            / src.constants.TOKEN_DECIMAL_FACTORS[token]
            * prices[token]
            for token, token_amount in self.collateral.token_amounts.items()
        )

    # TODO: Implement a dataclass for `prices`?
    def compute_risk_adjusted_collateral_usd(self, prices: Dict[str, decimal.Decimal]) -> decimal.Decimal:
        return sum(
            token_amount
            / src.constants.TOKEN_DECIMAL_FACTORS[token]
            * self.COLLATERAL_FACTORS[token]
            * prices[token]
            for token, token_amount in self.collateral.token_amounts.items()
        )

    # TODO: Force `DEBT_FACTORS` (=1 if irrelevant)?
    def compute_debt_usd(self, prices: Dict[str, decimal.Decimal]) -> decimal.Decimal:
        return sum(
            token_amount
            / src.constants.TOKEN_DECIMAL_FACTORS[token]
            * prices[token]
            for token, token_amount in self.debt.token_amounts.items()
        )

    # TODO: This method will likely differ across protocols. -> Leave empty?
    def compute_health_factor(
        self,
        prices: Optional[Dict[str, decimal.Decimal]] = None,
        # TODO: Use just `collateral_measure_usd` and `debt_measure_usd` and each protocol can use its own preferred 
        #  measure (risk-adjusted or non-adjusted)?
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_risk_adjusted_collateral_usd(prices = prices)
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(prices = prices)
        if debt_usd == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return risk_adjusted_collateral_usd / debt_usd

    # TODO: This method will likely differ across protocols. -> Leave empty?
    def compute_standardized_health_factor(
        self,
        prices: Optional[Dict[str, decimal.Decimal]] = None,
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_risk_adjusted_collateral_usd(prices = prices)
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(prices = prices)
        # Compute the value of (risk-adjusted) collateral at which the user/loan can be liquidated.
        collateral_usd_threshold = debt_usd
        if collateral_usd_threshold == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return risk_adjusted_collateral_usd / collateral_usd_threshold

    # TODO: This method will likely differ across protocols. -> Leave empty?
    def compute_debt_to_be_liquidated(
        self,
        debt_token: str,
        collateral_token: str,
        prices: Dict[str, decimal.Decimal],
        risk_adjusted_collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if risk_adjusted_collateral_usd is None:
            risk_adjusted_collateral_usd = self.compute_risk_adjusted_collateral_usd(prices = prices)
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(prices = prices)
        # TODO: Commit a PDF with the derivation of the formula?
        numerator = debt_usd - risk_adjusted_collateral_usd
        denominator = prices[debt_token] * (
            1
            - self.COLLATERAL_FACTORS[collateral_token] *
            (1 + self.LIQUIDATION_BONUSES[collateral_token])
        )
        return numerator / denominator

    def get_collateral_str(self) -> str:
        return ', '.join(
            f"{token}: {round(token_amount / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_amount in self.collateral.token_amounts.items()
            if token_amount > decimal.Decimal("0")
        )

    def get_debt_str(self) -> str:
        return ', '.join(
            f"{token}: {round(token_amount / src.constants.TOKEN_DECIMAL_FACTORS[token], 4)}"
            for token, token_amount in self.debt.token_amounts.items()
            if token_amount > decimal.Decimal("0")
        )

    def has_collateral(self) -> bool:
        if any(token_amount for token_amount in self.collateral.token_amounts.values()):
            return True
        return False

    def has_debt(self) -> bool:
        if any(token_amount for token_amount in self.debt.token_amounts.values()):
            return True
        return False


class State:
    """
    A class that describes the state of all loan entities of the given lending protocol.
    """

    EVENTS_METHODS_MAPPING: Dict[str, str] = {}

    # TODO: Fix the type of `loan_entity_class`.
    def __init__(
        self,
        loan_entity_class: Any,
        verbose_user: Optional[str] = None,
    ) -> None:
        self.loan_entity_class = loan_entity_class
        self.verbose_user = verbose_user
        self.loan_entities: collections.defaultdict = collections.defaultdict(self.loan_entity_class)
        self.last_block_number: int = 0

    def process_event(self, event: pandas.Series) -> None:
        # TODO: Save the timestamp of each update?
        assert event["block_number"] >= self.last_block_number
        self.last_block_number = event["block_number"]
        getattr(self, self.EVENTS_METHODS_MAPPING[event["key_name"]])(event=event)

    # TODO: This method will likely differ across protocols. -> Leave empty?
    def compute_liquidable_debt_at_price(
        self,
        prices: Dict[str, decimal.Decimal],
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices[collateral_token] = collateral_token_price
        max_liquidated_amount = decimal.Decimal("0")
        # TODO: for loan_entity in self.loan_entities.values(): + Search for other `for _, loan_entity`.
        for _, loan_entity in self.loan_entities.items():
            # Filter out entities who borrowed the token of interest.
            debt_tokens = {
                token
                for token, token_amount in loan_entity.debt.token_amounts.items()
                if token_amount > decimal.Decimal("0")
            }
            if not debt_token in debt_tokens:
                continue

            # Filter out entities with health factor below 1.
            risk_adjusted_collateral_usd = loan_entity.compute_risk_adjusted_collateral_usd(prices=changed_prices)
            debt_usd = loan_entity.compute_debt_usd(prices=changed_prices)
            health_factor = loan_entity.compute_health_factor(
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
            # TODO: `health_factor` < 0 should not be possible if the data is right. Should we keep the filter?
            if health_factor >= decimal.Decimal("1") or health_factor <= decimal.Decimal("0"):
                continue

            # Find out how much of the `debt_token` will be liquidated.
            collateral_tokens = {
                token
                for token, token_amount in loan_entity.collateral.token_amounts.items()
                if token_amount > decimal.Decimal("0")
            }
            # TODO: Choose the most optimal collateral_token to be liquidated. Or is the liquidator indifferent?
            collateral_token = list(collateral_tokens)[0]
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(
                debt_token=debt_token,
                collateral_token=collateral_token,
                prices=changed_prices,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )
        return max_liquidated_amount

    # TODO: This method will likely differ across protocols. -> Leave empty?
    def compute_number_of_active_loan_entities(self) -> int:
        return sum(
            loan_entity.has_collateral() or loan_entity.has_debt()
            for loan_entity in self.loan_entities.values()
        )

    # TODO: This method will likely differ across protocols. -> Leave empty?
    def compute_number_of_active_loan_entities_with_debt(self) -> int:
        return sum(loan_entity.has_debt() for loan_entity in self.loan_entities.values())