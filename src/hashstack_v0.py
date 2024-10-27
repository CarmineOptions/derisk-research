import copy
import dataclasses
import decimal
import logging
from typing import Optional

import pandas

import src.helpers
import src.settings
import src.state
import src.types

ADDRESS: str = "0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e"


@dataclasses.dataclass
class HashstackV0SpecificTokenSettings:
    # These are set to neutral values because Hashstack V0 doesn't use collateral factors.
    collateral_factor: decimal.Decimal
    # These are set to neutral values because Hashstack V0 doesn't use debt factors.
    debt_factor: decimal.Decimal


@dataclasses.dataclass
class TokenSettings(HashstackV0SpecificTokenSettings, src.settings.TokenSettings):
    pass


HASHSTACK_V0_SPECIFIC_TOKEN_SETTINGS: dict[str, HashstackV0SpecificTokenSettings] = {
    "ETH": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "WBTC": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDC": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "DAI": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDT": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    # TODO: Add wstETH.
    "wstETH": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    # TODO: Add LORDS.
    "LORDS": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    # TODO: Add STRK.
    "STRK": HashstackV0SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=src.settings.TOKEN_SETTINGS[token].symbol,
        decimal_factor=src.settings.TOKEN_SETTINGS[token].decimal_factor,
        address=src.settings.TOKEN_SETTINGS[token].address,
        collateral_factor=HASHSTACK_V0_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=HASHSTACK_V0_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
    )
    for token in src.settings.TOKEN_SETTINGS
}


# Keys are event names, values are names of the respective methods that process the given event.
EVENTS_TO_METHODS: dict[str, str] = {
    "new_loan": "process_new_loan_event",
    "collateral_added": "process_collateral_added_event",
    "collateral_withdrawal": "process_collateral_withdrawal_event",
    "loan_withdrawal": "process_loan_withdrawal_event",
    "loan_repaid": "process_loan_repaid_event",
    "loan_swap": "process_loan_swap_event",
    "loan_interest_deducted": "process_loan_interest_deducted_event",
    "liquidated": "process_liquidated_event",
}

# Keys are event names, values denote the order in which the given events should be processed.
HASHSTACK_V0_EVENTS_TO_ORDER: dict[str, str] = {
    "new_loan": 0,
    "loan_swap": 1,
    "liquidated": 2,
    "loan_withdrawal": 3,
    "loan_repaid": 4,
    "loan_interest_deducted": 5,
    "collateral_added": 6,
    "collateral_withdrawal": 7,
}


def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    events = src.helpers.get_events(
        addresses=(ADDRESS, ""),
        event_names=tuple(EVENTS_TO_METHODS),
        start_block_number=start_block_number,
    )
    # Ensure we're processing `loan_repaid` after other loan-altering events and the other events in a logical order.
    events["order"] = events["key_name"].map(HASHSTACK_V0_EVENTS_TO_ORDER)
    events.sort_values(["block_number", "transaction_hash", "order"], inplace=True)
    events.drop(columns=["order"], inplace=True)
    return events


class HashstackV0LoanEntity(src.types.LoanEntity):
    """
    A class that describes the Hashstack V0 loan entity. On top of the abstract `LoanEntity`, it implements the `user`,
    `debt_category`, `original_collateral` and `borrowed_collateral` attributes in order to help with accounting for
    the changes in collateral. This is because under Hashstack V0, each user can have multiple loans which are treated
    completely separately (including liquidations). The `debt_category` attribute determines liquidation conditions.
    Also, because Hashstack V0 provides leverage to its users, we split `collateral` into `original_collateral`
    (collateral deposited by the user directly) and `borrowed_collateral` (the current state, i.e. token and amount of
    the borrowed funds). We also use face amounts (no need to convert amounts using interest rates) because Hashstack
    V0 doesn't publish interest rate events.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self, user: str, debt_category: int) -> None:
        super().__init__()
        self.user: str = user
        self.debt_category: int = debt_category
        self.original_collateral: src.types.Portfolio = src.types.Portfolio()
        self.borrowed_collateral: src.types.Portfolio = src.types.Portfolio()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_model: Optional[src.types.InterestRateModels] = None,
        debt_interest_rate_model: Optional[src.types.InterestRateModels] = None,
        prices: Optional[src.types.Prices] = None,
        collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        pass  # TODO
        # if collateral_usd is None:
        #     collateral_usd = self.compute_collateral_usd(
        #         risk_adjusted = False,
        #         collateral_interest_rate_model = collateral_interest_rate_model,
        #         prices = prices,
        #     )
        # if debt_usd is None:
        #     debt_usd = self.compute_debt_usd(
        #         risk_adjusted = False,
        #         debt_interest_rate_model = debt_interest_rate_model,
        #         prices = prices,
        #     )
        # if standardized:
        #     # Denominator is the value of (risk-adjusted) collateral at which the loan entity can be liquidated.
        #     health_factor_liquidation_threshold = (
        #         decimal.Decimal("1.06")
        #         if self.debt_category == 1
        #         else decimal.Decimal("1.05")
        #         if self.debt_category == 2
        #         else decimal.Decimal("1.04")
        #     )
        #     denominator = health_factor_liquidation_threshold * debt_usd
        # else:
        #     denominator = debt_usd
        # if denominator == decimal.Decimal("0"):
        #     # TODO: Assumes collateral is positive.
        #     return decimal.Decimal("Inf")
        # return collateral_usd / denominator

    def compute_debt_to_be_liquidated(
        self,
        debt_interest_rate_model: Optional[src.types.InterestRateModels] = None,
        prices: Optional[src.types.Prices] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        pass  # TODO
        # if debt_usd is None:
        #     debt_usd = self.compute_debt_usd(
        #         risk_adjusted = False,
        #         debt_interest_rate_model = debt_interest_rate_model,
        #         prices = prices,
        #     )
        # return debt_usd


class HashstackV0State(src.state.State):
    """
    A class that describes the state of all Hashstack V0 loan entities. It implements a method for correct processing
    of every relevant event. Hashstack V0 events always contain the final state of the loan entity's collateral and
    debt, thus we always rewrite the balances whenever they are updated.
    """

    EVENTS_TO_METHODS: dict[str, str] = EVENTS_TO_METHODS

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=HashstackV0LoanEntity,
            verbose_user=verbose_user,
        )

    # TODO: Reduce most of the events processing to `rewrite_original_collateral`, `rewrite_borrowed_collateral`, and
    # `rewrite_debt`?

    def process_new_loan_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`collateral`] `market`, `amount`, ``, `current_amount`, ``, `commitment`,
        # `timelock_validity`, `is_timelock_activated`, `activation_time`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x04ff9acb9154603f1fc14df328a3ea53a6c58087aaac0bfbe9cc7f2565777db8_2.
        loan_id = int(event["data"][0], base=16)
        user = src.helpers.add_leading_zeros(event["data"][1])
        debt_token = src.helpers.get_symbol(event["data"][2])
        debt_face_amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        borrowed_collateral_token = src.helpers.get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        debt_category = int(event["data"][10], base=16)
        # Several initial loans have different structure of 'data'.
        try:
            original_collateral_token = src.helpers.get_symbol(event["data"][14])
            original_collateral_face_amount = decimal.Decimal(
                str(int(event["data"][17], base=16))
            )
        except KeyError:
            original_collateral_token = src.helpers.get_symbol(event["data"][13])
            original_collateral_face_amount = decimal.Decimal(
                str(int(event["data"][16], base=16))
            )

        self.loan_entities[loan_id] = HashstackV0LoanEntity(
            user=user, debt_category=debt_category
        )
        # TODO: Make it possible to initialize src.types.Portfolio with some token amount directly.
        original_collateral = src.types.Portfolio()
        original_collateral[original_collateral_token] = original_collateral_face_amount
        self.loan_entities[loan_id].original_collateral = original_collateral
        borrowed_collateral = src.types.Portfolio()
        borrowed_collateral[borrowed_collateral_token] = borrowed_collateral_face_amount
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        # TODO: Make it easier to sum 2 src.types.Portfolio instances.
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        debt = src.types.Portfolio()
        debt[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, face amount = {} of token = {} was borrowed against original collateral face "
                "amount = {} of token = {} and borrowed collateral face amount = {} of token = {}.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    original_collateral_face_amount,
                    original_collateral_token,
                    original_collateral_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )

    def process_collateral_added_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`collateral_record`] `market`, `amount`, ``,
        # `current_amount`, ``, `commitment`, `timelock_validity`, `is_timelock_activated`, `activation_time`,
        # [`loan_id`] `loan_id`, [`amount_added`] `amount_added`, ``, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x02df71b02fce15f2770533328d1e645b957ac347d96bd730466a2e087f24ee07_2.
        loan_id = int(event["data"][9], base=16)
        original_collateral_token = src.helpers.get_symbol(event["data"][0])
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )
        original_collateral = src.types.Portfolio()
        original_collateral[original_collateral_token] = original_collateral_face_amount
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was added, resulting in collateral of face amount = {} of token = "
                "{}.".format(
                    event["block_number"],
                    original_collateral_face_amount,
                    original_collateral_token,
                )
            )

    def process_collateral_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`collateral_record`] `market`, `amount`, ``,
        # `current_amount`, ``, `commitment`, `timelock_validity`, `is_timelock_activated`, `activation_time`,
        # [`loan_id`] `loan_id`, [`amount_withdrawn`] `amount_withdrawn`, ``, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x03809ebcaad1647f2c6d5294706e0dc619317c240b5554848c454683a18b75ba_5.
        loan_id = int(event["data"][9], base=16)
        original_collateral_token = src.helpers.get_symbol(event["data"][0])
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )
        original_collateral = src.types.Portfolio()
        original_collateral[original_collateral_token] = original_collateral_face_amount
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was withdrawn, resulting in collateral of face amount = {} of token "
                "= {}.".format(
                    event["block_number"],
                    original_collateral_face_amount,
                    original_collateral_token,
                )
            )

    def process_loan_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`amount_withdrawn`] `amount_withdrawn`, ``, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x05bb8614095fac1ac9b405c27e7ce870804e85aa5924ef2494fec46792b6b8dc_2.
        loan_id = int(event["data"][0], base=16)
        user = src.helpers.add_leading_zeros(event["data"][1])
        # TODO: Is this assert needed?
        assert self.loan_entities[loan_id].user == user
        debt_token = src.helpers.get_symbol(event["data"][2])
        debt_face_amount = decimal.Decimal(str(int(event["data"][4], base=16)))
        borrowed_collateral_token = src.helpers.get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        debt_category = int(event["data"][10], base=16)

        borrowed_collateral = src.types.Portfolio()
        borrowed_collateral[borrowed_collateral_token] = borrowed_collateral_face_amount
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        debt = src.types.Portfolio()
        debt[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        self.loan_entities[loan_id].debt_category = debt_category
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was withdrawn, resulting in debt of face amount = {} of token = {} and "
                "borrowed collateral of face amount = {} of token = {}.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )

    def process_loan_repaid_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x07731e48d33f6b916f4e4e81e9cee1d282e20e970717e11ad440f73cc1a73484_1.
        loan_id = int(event["data"][0], base=16)
        user = src.helpers.add_leading_zeros(event["data"][1])
        assert self.loan_entities[loan_id].user == user
        debt_token = src.helpers.get_symbol(event["data"][2])
        # This prevents repaid loans to appear as not repaid.
        debt_face_amount = decimal.Decimal("0")
        borrowed_collateral_token = src.helpers.get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        # Based on the documentation, it seems that it's only possible to repay the whole amount.
        assert borrowed_collateral_face_amount == decimal.Decimal("0")
        debt_category = int(event["data"][10], base=16)

        borrowed_collateral = src.types.Portfolio()
        borrowed_collateral[borrowed_collateral_token] = borrowed_collateral_face_amount
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        debt = src.types.Portfolio()
        debt[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        self.loan_entities[loan_id].debt_category = debt_category
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was repaid, resulting in debt of face amount = {} of token = {} and "
                "borrowed collateral of face amount = {} of token = {}.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )

    def process_loan_swap_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`old_loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`new_loan_record`] `id`, `owner`, `market`, `commitment`, `amount`, ``,
        # `current_market`, `current_amount`, ``, `is_loan_withdrawn`, `debt_category`, `state`, `l3_integration`,
        # `created_at`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x00ad0b6b00ce68a1d7f5b79cd550d7f4a15b1708b632b88985a4f6faeb42d5b1_7.
        old_loan_id = int(event["data"][0], base=16)
        old_user = src.helpers.add_leading_zeros(event["data"][1])
        assert self.loan_entities[old_loan_id].user == old_user
        new_loan_id = int(event["data"][14], base=16)
        new_user = src.helpers.add_leading_zeros(event["data"][15])
        # TODO: Does this always have to hold?
        assert new_loan_id == old_loan_id
        # TODO: Does this always have to hold?
        assert new_user == old_user
        new_debt_token = src.helpers.get_symbol(event["data"][16])
        new_debt_face_amount = decimal.Decimal(str(int(event["data"][18], base=16)))
        new_borrowed_collateral_token = src.helpers.get_symbol(event["data"][20])
        new_borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][21], base=16))
        )
        new_debt_category = int(event["data"][24], base=16)

        new_borrowed_collateral = src.types.Portfolio()
        new_borrowed_collateral[new_borrowed_collateral_token] = (
            new_borrowed_collateral_face_amount
        )
        self.loan_entities[new_loan_id].borrowed_collateral = new_borrowed_collateral
        self.loan_entities[new_loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[new_loan_id].original_collateral[token]
                    + self.loan_entities[new_loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[new_loan_id].original_collateral,
                    self.loan_entities[new_loan_id].borrowed_collateral,
                )
            }
        )
        new_debt = src.types.Portfolio()
        new_debt[new_debt_token] = new_debt_face_amount
        # Based on the documentation, it seems that it's only possible to swap the whole amount.
        assert self.loan_entities[old_loan_id].debt == new_debt
        self.loan_entities[new_loan_id].debt = new_debt
        self.loan_entities[new_loan_id].debt_category = new_debt_category
        if self.loan_entities[new_loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was swapped, resulting in debt of face amount = {} of token = {} and "
                "borrowed collateral of face amount = {} of token = {}.".format(
                    event["block_number"],
                    new_debt_face_amount,
                    new_debt_token,
                    new_borrowed_collateral_face_amount,
                    new_borrowed_collateral_token,
                )
            )

    def process_loan_interest_deducted_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`collateral_record`] `market`, `amount`, ``,
        # `current_amount`, ``, `commitment`, `timelock_validity`, `is_timelock_activated`, `activation_time`,
        # [`accrued_interest`] `accrued_interest`, ``, [`loan_id`] `loan_id`, [`amount_withdrawn`] `amount_withdrawn`,
        # ``, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x050db0ed93d7abbfb152e16608d4cf4dbe0b686b134f890dd0ad8418b203c580_2.
        loan_id = int(event["data"][11], base=16)
        original_collateral_token = src.helpers.get_symbol(event["data"][0])
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )
        original_collateral = src.types.Portfolio()
        original_collateral[original_collateral_token] = original_collateral_face_amount
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan interest was deducted, resulting in collateral of face amount = {} of "
                "token = {}.".format(
                    event["block_number"],
                    original_collateral_face_amount,
                    original_collateral_token,
                )
            )

    def process_liquidated_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_record`] `id`, `owner`, `market`, `commitment`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `is_loan_withdrawn`, `debt_category`, `state`,
        # `l3_integration`, `created_at`, [`liquidator`] `liquidator`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x0774bebd15505d3f950c362d813dc81c6320ae92cb396b6469fd1ac5d8ff62dc_8.
        loan_id = int(event["data"][0], base=16)
        user = src.helpers.add_leading_zeros(event["data"][1])
        assert self.loan_entities[loan_id].user == user
        debt_token = src.helpers.get_symbol(event["data"][2])
        # This prevents liquidated loans to appear as not repaid.
        debt_face_amount = decimal.Decimal("0")
        borrowed_collateral_token = src.helpers.get_symbol(event["data"][6])
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][7], base=16))
        )
        # Based on the documentation, it seems that it's only possible to liquidate the whole amount.
        assert borrowed_collateral_face_amount == decimal.Decimal("0")
        debt_category = int(event["data"][10], base=16)

        borrowed_collateral = src.types.Portfolio()
        borrowed_collateral[borrowed_collateral_token] = borrowed_collateral_face_amount
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        # TODO: What happens to original collateral? For now, let's assume it disappears.
        original_collateral = src.types.Portfolio()
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral = src.types.Portfolio(
            **{
                token: (
                    self.loan_entities[loan_id].original_collateral[token]
                    + self.loan_entities[loan_id].borrowed_collateral[token]
                )
                for token in set().union(
                    self.loan_entities[loan_id].original_collateral,
                    self.loan_entities[loan_id].borrowed_collateral,
                )
            }
        )
        debt = src.heltypespers.Portfolio()
        debt[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        self.loan_entities[loan_id].debt_category = debt_category
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was liquidated, resulting in debt of face amount = {} of token = {}, "
                "borrowed collateral of face amount = {} of token = {} and no original collateral.".format(
                    event["block_number"],
                    debt_face_amount,
                    debt_token,
                    borrowed_collateral_face_amount,
                    borrowed_collateral_token,
                )
            )

    async def collect_token_parameters(self) -> None:
        # Get the sets of unique collateral and debt tokens.
        collateral_tokens = {
            y for x in self.loan_entities.values() for y in x.collateral.keys()
        }
        debt_tokens = {y for x in self.loan_entities.values() for y in x.debt.keys()}
        logging.error("{} {}".format(collateral_tokens, debt_tokens))

    #     # Get parameters for each collateral and debt token. Under zkLend, the collateral token in the events data is
    #     # the underlying token directly.
    #     for underlying_collateral_token_address in collateral_tokens:
    #         underlying_collateral_token_symbol = await src.helpers.get_symbol(
    #             token_address=underlying_collateral_token_address
    #         )
    #         # The order of the arguments is: `enabled`, `decimals`, `z_token_address`, `interest_rate_model`,
    #         # `collateral_factor`, `borrow_factor`, `reserve_factor`, `last_update_timestamp`, `lending_accumulator`,
    #         # `debt_accumulator`, `current_lending_rate`, `current_borrowing_rate`, `raw_total_debt`, `flash_loan_fee`,
    #         # `liquidation_bonus`, `debt_limit`.
    #         reserve_data = await src.blockchain_call.func_call(
    #             addr=ZKLEND_MARKET,
    #             selector="get_reserve_data",
    #             calldata=[underlying_collateral_token_address],
    #         )
    #         collateral_token_address = src.helpers.add_leading_zeros(
    #             hex(reserve_data[2])
    #         )
    #         collateral_token_symbol = await src.helpers.get_symbol(
    #             token_address=collateral_token_address
    #         )
    #         self.collateral[underlying_collateral_token_address] = (
    #             ZkLendCollateralTokenParameters(
    #                 address=collateral_token_address,
    #                 decimals=int(reserve_data[1]),
    #                 symbol=collateral_token_symbol,
    #                 underlying_symbol=underlying_collateral_token_symbol,
    #                 underlying_address=underlying_collateral_token_address,
    #                 collateral_factor=decimal.Decimal(reserve_data[4]),
    #                 liquidation_bonus=decimal.Decimal(reserve_data[14]),
    #             )
    #         )
    #     for underlying_debt_token_address in debt_tokens:
    #         underlying_debt_token_symbol = await src.helpers.get_symbol(
    #             token_address=underlying_debt_token_address
    #         )
    #         # The order of the arguments is: `enabled`, `decimals`, `z_token_address`, `interest_rate_model`,
    #         # `collateral_factor`, `borrow_factor`, `reserve_factor`, `last_update_timestamp`, `lending_accumulator`,
    #         # `debt_accumulator`, `current_lending_rate`, `current_borrowing_rate`, `raw_total_debt`, `flash_loan_fee`,
    #         # `liquidation_bonus`, `debt_limit`.
    #         reserve_data = await src.blockchain_call.func_call(
    #             addr=ZKLEND_MARKET,
    #             selector="get_reserve_data",
    #             calldata=[underlying_debt_token_address],
    #         )
    #         debt_token_address = src.helpers.add_leading_zeros(hex(reserve_data[2]))
    #         debt_token_symbol = await src.helpers.get_symbol(
    #             token_address=debt_token_address
    #         )
    #         self.debt[underlying_debt_token_address] = ZkLendDebtTokenParameters(
    #             address=debt_token_address,
    #             decimals=int(reserve_data[1]),
    #             symbol=debt_token_symbol,
    #             underlying_symbol=underlying_debt_token_symbol,
    #             underlying_address=underlying_debt_token_address,
    #             debt_factor=decimal.Decimal(reserve_data[5]),
    #         )

    def compute_liquidable_debt_at_price(
        self,
        prices: src.types.Prices,
        collateral_token: str,
        collateral_token_price: float,
        debt_token: str,
    ) -> decimal.Decimal:
        pass  # TODO
        # changed_prices = copy.deepcopy(prices)
        # changed_prices[collateral_token] = collateral_token_price
        # max_liquidated_amount = decimal.Decimal("0")
        # for loan_entity in self.loan_entities.values():
        #     # Filter out users who borrowed the token of interest.
        #     debt_tokens = {
        #         token
        #         for token, token_amount in loan_entity.debt.items()
        #         if token_amount > decimal.Decimal("0")
        #     }
        #     if not debt_token in debt_tokens:
        #         continue

        #     # Filter out users with health factor below 1.
        #     debt_usd = loan_entity.compute_debt_usd(
        #         risk_adjusted=False,
        #         debt_interest_rate_model=self.interest_rate_model.debt,
        #         prices=changed_prices,
        #     )
        #     health_factor = loan_entity.compute_health_factor(
        #         standardized=False,
        #         collateral_interest_rate_model=self.interest_rate_model.collateral,
        #         prices=changed_prices,
        #         debt_usd=debt_usd,
        #     )
        #     health_factor_liquidation_threshold = (
        #         decimal.Decimal("1.06")
        #         if loan_entity.debt_category == 1
        #         else decimal.Decimal("1.05")
        #         if loan_entity.debt_category == 2
        #         else decimal.Decimal("1.04")
        #     )
        #     if health_factor >= health_factor_liquidation_threshold:
        #         continue

        #     # Find out how much of the `debt_token` will be liquidated.
        #     max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(debt_usd=debt_usd)
        # return max_liquidated_amount

    def compute_number_of_active_users(self) -> int:
        unique_active_users = {
            loan_entity.user
            for loan_entity in self.loan_entities.values()
            if loan_entity.has_collateral() or loan_entity.has_debt()
        }
        return len(unique_active_users)

    def compute_number_of_active_borrowers(self) -> int:
        unique_active_borrowers = {
            loan_entity.user
            for loan_entity in self.loan_entities.values()
            if loan_entity.has_debt()
        }
        return len(unique_active_borrowers)
