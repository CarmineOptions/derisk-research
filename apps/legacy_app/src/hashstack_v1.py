import copy
import dataclasses
import decimal
import logging
from typing import Optional

import pandas

import src.helpers
import src.settings
import src.state
import src.swap_amm
import src.types

R_TOKENS: dict[str, str] = {
    "ETH": "0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e",
    "USDC": "0x03bcecd40212e9b91d92bbe25bb3643ad93f0d230d93237c675f46fac5187e8c",
    "USDT": "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21",
    "DAI": "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f",
    "WBTC": "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef",
}


ADDRESSES_TO_TOKENS: dict[str, str] = {
    "0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e": "ETH",
    "0x03bcecd40212e9b91d92bbe25bb3643ad93f0d230d93237c675f46fac5187e8c": "USDC",
    "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21": "USDT",
    "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f": "DAI",
    "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef": "WBTC",
    "0x01ef7f9f8bf01678dc6d27e2c26fb7e8eac3812a24752e6a1d6a49d153bec9f3": "ETH",
    "0x021d8d8519f5464ec63c6b9a80a5229c5ddeed57ecded4c8a9dfc34e31b49990": "USDC",
    "0x012b8185e237dd0340340faeb3351dbe53f8a42f5a9bf974ddf90ced56e301c7": "USDT",
    "0x07eeed99c095f83716e465e2c52a3ec8f47b323041ddc4f97778ac0393b7f358": "DAI",
    "0x02614c784267d2026042ab98588f90efbffaade8982567e93530db4ed41201cf": "WBTC",
    # JediSwap pools.
    "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138": "JediSwap: DAI/ETH Pool",
    "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b": "JediSwap: DAI/USDC Pool",
    "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767": "JediSwap: DAI/USDT Pool",
    "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a": "JediSwap: ETH/USDC Pool",
    "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6": "JediSwap: ETH/USDT Pool",
    "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b": "JediSwap: USDC/USDT Pool",
    "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c": "JediSwap: WBTC/ETH Pool",
    "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8": "JediSwap: WBTC/USDC Pool",
    "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0": "JediSwap: WBTC/USDT Pool",
    # MySwap pools.
    "0x07c662b10f409d7a0a69c8da79b397fd91187ca5f6230ed30effef2dceddc5b3": "mySwap: DAI/ETH Pool",
    "0x0611e8f4f3badf1737b9e8f0ca77dd2f6b46a1d33ce4eed951c6b18ac497d505": "mySwap: DAI/USDC Pool",
    "0x022b05f9396d2c48183f6deaf138a57522bcc8b35b67dee919f76403d1783136": "mySwap: ETH/USDC Pool",
    "0x041f9a1e9a4d924273f5a5c0c138d52d66d2e6a8bee17412c6b0f48fe059ae04": "mySwap: ETH/USDT Pool",
    "0x01ea237607b7d9d2e9997aa373795929807552503683e35d8739f4dc46652de1": "mySwap: USDC/USDT Pool",
    "0x025b392609604c75d62dde3d6ae98e124a31b49123b8366d7ce0066ccb94f696": "mySwap: WBTC/USDC Pool",
    # TODO: Non-Hashstack specific tokens. This mapping duplicates information from `TOKEN_SETTINGS`.
    "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3": "DAI",
    "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": "ETH",
    "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": "USDC",
    "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8": "USDT",
    "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac": "WBTC",
}


@dataclasses.dataclass
class HashstackV1SpecificTokenSettings:
    # These are set to neutral values because Hashstack V1 doesn't use collateral factors.
    collateral_factor: decimal.Decimal
    # These are set to neutral values because Hashstack V1 doesn't use debt factors.
    debt_factor: decimal.Decimal


@dataclasses.dataclass
class TokenSettings(HashstackV1SpecificTokenSettings, src.settings.TokenSettings):
    pass


HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS: dict[str, src.settings.TokenSettings] = {
    "JediSwap: DAI/ETH Pool": src.settings.TokenSettings(
        symbol="JediSwap: DAI/ETH Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
    ),
    "JediSwap: DAI/USDC Pool": src.settings.TokenSettings(
        symbol="JediSwap: DAI/USDC Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
    ),
    "JediSwap: DAI/USDT Pool": src.settings.TokenSettings(
        symbol="JediSwap: DAI/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
    ),
    "JediSwap: ETH/USDC Pool": src.settings.TokenSettings(
        symbol="JediSwap: ETH/USDC Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    ),
    "JediSwap: ETH/USDT Pool": src.settings.TokenSettings(
        symbol="JediSwap: ETH/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
    ),
    "JediSwap: USDC/USDT Pool": src.settings.TokenSettings(
        symbol="JediSwap: USDC/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
    ),
    "JediSwap: WBTC/ETH Pool": src.settings.TokenSettings(
        symbol="JediSwap: WBTC/ETH Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
    ),
    "JediSwap: WBTC/USDC Pool": src.settings.TokenSettings(
        symbol="JediSwap: WBTC/USDC Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
    ),
    "JediSwap: WBTC/USDT Pool": src.settings.TokenSettings(
        symbol="JediSwap: WBTC/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
    ),
    "mySwap: DAI/ETH Pool": src.settings.TokenSettings(
        symbol="mySwap: DAI/ETH Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x07c662b10f409d7a0a69c8da79b397fd91187ca5f6230ed30effef2dceddc5b3",
    ),
    "mySwap: DAI/USDC Pool": src.settings.TokenSettings(
        symbol="mySwap: DAI/USDC Pool",
        decimal_factor=decimal.Decimal("1e12"),
        address="0x0611e8f4f3badf1737b9e8f0ca77dd2f6b46a1d33ce4eed951c6b18ac497d505",
    ),
    "mySwap: ETH/USDC Pool": src.settings.TokenSettings(
        symbol="mySwap: ETH/USDC Pool",
        decimal_factor=decimal.Decimal("1e12"),
        address="0x022b05f9396d2c48183f6deaf138a57522bcc8b35b67dee919f76403d1783136",
    ),
    "mySwap: ETH/USDT Pool": src.settings.TokenSettings(
        symbol="mySwap: ETH/USDT Pool",
        decimal_factor=decimal.Decimal("1e12"),
        address="0x041f9a1e9a4d924273f5a5c0c138d52d66d2e6a8bee17412c6b0f48fe059ae04",
    ),
    "mySwap: USDC/USDT Pool": src.settings.TokenSettings(
        symbol="mySwap: USDC/USDT Pool",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x01ea237607b7d9d2e9997aa373795929807552503683e35d8739f4dc46652de1",
    ),
    "mySwap: WBTC/USDC Pool": src.settings.TokenSettings(
        symbol="mySwap: WBTC/USDC Pool",
        decimal_factor=decimal.Decimal("1e7"),
        address="0x025b392609604c75d62dde3d6ae98e124a31b49123b8366d7ce0066ccb94f696",
    ),
}
HASHSTACK_V1_SPECIFIC_TOKEN_SETTINGS: dict[str, HashstackV1SpecificTokenSettings] = {
    "ETH": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "WBTC": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDC": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "DAI": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDT": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    # TODO: Add wstETH.
    "wstETH": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    # TODO: Add LORDS.
    "LORDS": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    # TODO: Add STRK.
    "STRK": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: DAI/ETH Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: DAI/USDC Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: DAI/USDT Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: ETH/USDC Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: ETH/USDT Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: USDC/USDT Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: WBTC/ETH Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: WBTC/USDC Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: WBTC/USDT Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: DAI/ETH Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: DAI/USDC Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: ETH/USDC Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: ETH/USDT Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: USDC/USDT Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: WBTC/USDC Pool": HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=token_settings.symbol,
        decimal_factor=token_settings.decimal_factor,
        address=token_settings.address,
        collateral_factor=HASHSTACK_V1_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=HASHSTACK_V1_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
    )
    for token, token_settings in (
        src.settings.TOKEN_SETTINGS | HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS
    ).items()
}


# Keys are event names, values are names of the respective methods that process the given event.
EVENTS_TO_METHODS: dict[str, str] = {
    "new_loan": "process_new_loan_event",
    "collateral_added": "process_collateral_added_event",
    "loan_spent": "process_loan_spent_event",
    "loan_transferred": "process_loan_transferred_event",
    "loan_repaid": "process_loan_repaid_event",
}

# Keys are event names, values denote the order in which the given events should be processed.
HASHSTACK_V1_EVENTS_TO_ORDER: dict[str, str] = {
    "new_loan": 0,
    "loan_transferred": 1,
    "loan_spent": 2,
    "loan_repaid": 3,
    "collateral_added": 4,
}


def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    events = src.helpers.get_events(
        addresses=tuple(ADDRESSES_TO_TOKENS),
        event_names=tuple(EVENTS_TO_METHODS),
        start_block_number=start_block_number,
    )
    # Ensure we're processing `loan_repaid` after other loan-altering events and the other events in a logical order.
    # Sometimes, when a user deposits tokens, borrows against them and then e.g. spends the borrowed funds in the same
    # block, the whole operation is split into multiple transactions. Since we don't have any way to order transactions
    # themselves, we need to order strictly according to our own `order` column.
    events["order"] = events["key_name"].map(HASHSTACK_V1_EVENTS_TO_ORDER)
    events.sort_values(["block_number", "order"], inplace=True)
    return events


class HashstackV1LoanEntity(src.types.LoanEntity):
    """
    A class that describes the Hashstack V1 loan entity. On top of the abstract `LoanEntity`, it implements the `user`,
    `original_collateral` and `borrowed_collateral` attributes in order to help with accounting for the changes in
    collateral. This is because under Hashstack V1, each user can have multiple loans which are treated completely
    separately (including liquidations). Also, because Hashstack V1 provides leverage to its users, we split
    `collateral` into `original_collateral` (collateral deposited by the user directly) and `borrowed_collateral` (the
    current state, i.e. token and amount of the borrowed funds). We also use face amounts (no need to convert amounts
    using interest rates) because Hashstack V1 doesn't publish interest rate events.
    """

    # TODO: Confirm that Hashstack V1 doesn't publish interest rate events.

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self, user: str) -> None:
        super().__init__()
        self.user: str = user
        self.original_collateral: src.types.Portfolio = src.types.Portfolio()
        self.borrowed_collateral: src.types.Portfolio = src.types.Portfolio()
        self.collateral: src.types.Portfolio = src.types.Portfolio()
        self.debt: src.types.Portfolio = src.types.Portfolio()

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
        #     # TODO: Does this parameter still hold?
        #     denominator = decimal.Decimal("1.04") * debt_usd
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
        # # TODO: Has the liquidation mechanism changed?
        # if debt_usd is None:
        #     debt_usd = self.compute_debt_usd(
        #         risk_adjusted = False,
        #         debt_interest_rate_model = debt_interest_rate_model,
        #         prices = prices,
        #     )
        # return debt_usd


class HashstackV1State(src.state.State):
    """
    A class that describes the state of all Hashstack V1 loan entities. It implements a method for correct processing
    of every relevant event. Hashstack V1 events always contain the final state of the loan entity's collateral and
    debt, thus we always rewrite the balances whenever they are updated.
    """

    ADDRESSES_TO_TOKENS: dict[str, str] = ADDRESSES_TO_TOKENS
    EVENTS_TO_METHODS: dict[str, str] = EVENTS_TO_METHODS

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=HashstackV1LoanEntity,
            verbose_user=verbose_user,
        )

    # TODO: There appears to be some overlap with HashstackV0State. Can we simplify the code?
    # TODO: Reduce most of the events processing to `rewrite_original_collateral`, `rewrite_borrowed_collateral`, and
    # `rewrite_debt`?

    def process_new_loan_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_record`] `loan_id`, `borrower`, `market`, `amount`,
        # ``, `current_market`, `current_amount`, ``, `state`, `l3_integration`, `l3_category`, `created_at`,
        # [`collateral`] `loan_id`, `collateral_token`, `amount`, ``, `created_at`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x00085b80dbb6c3cb161bb2b73ebc8c3b3b806395fc5c9a0f110ae2a1fa04a578_9.
        loan_id = int(event["data"][0], base=16)
        collateral_loan_id = int(event["data"][12], base=16)
        assert loan_id == collateral_loan_id
        user = src.helpers.add_leading_zeros(event["data"][1])

        debt_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][2])
        ]
        debt_face_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        borrowed_collateral_token = src.helpers.get_symbol(
            src.helpers.add_leading_zeros(event["data"][5])
        )
        borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][6], base=16))
        )
        original_collateral_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][13])
        ]
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][14], base=16))
        )

        self.loan_entities[loan_id] = HashstackV1LoanEntity(user=user)
        # TODO: Make it possible to initialize `src.types.Portfolio`` with some token amount directly.
        original_collateral = src.types.Portfolio()
        original_collateral[original_collateral_token] = original_collateral_face_amount
        self.loan_entities[loan_id].original_collateral = original_collateral
        borrowed_collateral = src.types.Portfolio()
        borrowed_collateral[borrowed_collateral_token] = borrowed_collateral_face_amount
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        # TODO: Make it easier to sum 2 `src.types.Portfolio` instances.
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
        # The order of the values in the `data` column is: [`collateral_record`] `loan_id`, `collateral_token`,
        # `amount`, ``, `created_at`, [`amount_added`] `amount_added`, ``, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x027b7e40273848af37e092eaec38311ac1d2e6c3fc2724020736e9f322b6fcf7_0.
        loan_id = int(event["data"][0], base=16)

        original_collateral_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][1])
        ]
        original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][2], base=16))
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

    def process_loan_spent_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`old_loan_record`] `loan_id`, `borrower`, `market`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `state`, `l3_integration`, `l3_category`, `created_at`,
        # [`new_loan_record`] `loan_id`, `borrower`, `market`, `amount`, ``, `current_market`, `current_amount`, ``,
        # `state`, `l3_integration`, `l3_category`, `created_at`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x0051f75ef1e08f70d1c8efe7866384d026aa0ca092ded8bd1c903aac0478b990_25.
        old_loan_id = int(event["data"][0], base=16)
        old_user = src.helpers.add_leading_zeros(event["data"][1])
        assert self.loan_entities[old_loan_id].user == old_user
        new_loan_id = int(event["data"][12], base=16)
        new_user = src.helpers.add_leading_zeros(event["data"][13])
        # TODO: Does this always have to hold?
        assert new_loan_id == old_loan_id
        # TODO: Does this always have to hold?
        assert new_user == old_user

        new_debt_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][14])
        ]
        new_debt_face_amount = decimal.Decimal(str(int(event["data"][15], base=16)))
        new_borrowed_collateral_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][17])
        ]
        new_borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][18], base=16))
        )

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
        # Based on the documentation, it seems that it's only possible to spend the whole amount.
        assert self.loan_entities[old_loan_id].debt == new_debt
        self.loan_entities[new_loan_id].debt = new_debt
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

    def process_loan_transferred_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_id`] `loan_id`, [`sender`] `sender`, [`reciever`]
        # `reciever`, [`timestamp`] `timestamp`.
        # Example: https://starkscan.co/event/0x028ea2b3cb9759214c7ea18e86a2d1b33a4bf3f87b4b0b4eb75919c9ab87a62e_5.
        loan_id = int(event["data"][0], base=16)
        old_user = src.helpers.add_leading_zeros(event["data"][1])
        assert self.loan_entities[loan_id].user == old_user
        new_user = src.helpers.add_leading_zeros(event["data"][2])
        self.loan_entities[loan_id].user = new_user
        if self.verbose_user in {old_user, self.loan_entities[loan_id].user}:
            logging.info(
                "In block number = {}, loan was transferred from user = {} to user = {}.".format(
                    event["block_number"],
                    old_user,
                    new_user,
                )
            )

    def process_loan_repaid_event(self, event: pandas.Series) -> None:
        # The order of the values in the `data` column is: [`loan_record`] `loan_id`, `borrower`, `market`, `amount`,
        # ``, `current_market`, `current_amount`, ``, `state`, `l3_integration`, `l3_category`, `created_at`,
        # [`new_loan_record`] `loan_id`, `borrower`, `market`, `amount`, ``, `current_market`, `current_amount`, ``,
        # `state`, `l3_integration`, `l3_category`, `created_at`, [`collateral_record`] `loan_id`, `collateral_token`,
        # `amount`, ``, `created_at`, [`totalUserDebt`] `totalUserDebt`, [`deficit`] `deficit`, [`timestamp`]
        # `timestamp`.
        # Example: https://starkscan.co/event/0x0069ff177c728aae4248ba8625322f75f0c5df918215f9e5dee10fe22c1fa26c_53.
        old_loan_id = int(event["data"][0], base=16)
        old_user = src.helpers.add_leading_zeros(event["data"][1])
        assert self.loan_entities[old_loan_id].user == old_user
        new_loan_id = int(event["data"][12], base=16)
        new_user = src.helpers.add_leading_zeros(event["data"][13])
        # TODO: Does this always have to hold?
        assert new_loan_id == old_loan_id
        # TODO: Does this always have to hold?
        assert new_user == old_user
        new_collateral_loan_id = int(event["data"][24], base=16)
        assert new_loan_id == new_collateral_loan_id

        new_debt_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][14])
        ]
        new_debt_face_amount = decimal.Decimal(str(int(event["data"][15], base=16)))
        new_borrowed_collateral_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][17])
        ]
        new_borrowed_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][18], base=16))
        )
        new_original_collateral_token = self.ADDRESSES_TO_TOKENS[
            src.helpers.add_leading_zeros(event["data"][25])
        ]
        new_original_collateral_face_amount = decimal.Decimal(
            str(int(event["data"][26], base=16))
        )
        # Based on the documentation, it seems that it's only possible to repay the whole amount.
        assert new_debt_face_amount == decimal.Decimal("0")
        assert new_borrowed_collateral_face_amount == decimal.Decimal("0")
        assert new_original_collateral_face_amount == decimal.Decimal("0")

        new_original_collateral = src.types.Portfolio()
        new_original_collateral[new_original_collateral_token] = (
            new_original_collateral_face_amount
        )
        new_borrowed_collateral = src.types.Portfolio()
        new_borrowed_collateral[new_borrowed_collateral_token] = (
            new_borrowed_collateral_face_amount
        )
        self.loan_entities[new_loan_id].original_collateral = new_original_collateral
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
        self.loan_entities[new_loan_id].debt = new_debt
        if self.loan_entities[new_loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, loan was repaid, resulting in debt of face amount = {} of token = {} and "
                "original collateral face amount = {} of token = {} and borrowed collateral of face amount = {} of "
                "token = {}.".format(
                    event["block_number"],
                    new_debt_face_amount,
                    new_debt_token,
                    new_borrowed_collateral_face_amount,
                    new_original_collateral_token,
                    new_borrowed_collateral_face_amount,
                    new_borrowed_collateral_token,
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
        #     # TODO: Does this parameter still hold?
        #     if health_factor >= decimal.Decimal("1.04"):
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
