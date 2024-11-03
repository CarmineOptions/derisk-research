"""
Event handling and state management for Hashstack V1, including token settings, portfolios, and loan entity updates.
"""
import copy
import dataclasses
import decimal
import logging
from typing import Optional

import pandas as pd
from data_handler.handlers.helpers import MAX_ROUNDING_ERRORS, get_symbol
from data_handler.handlers.settings import TokenSettings

from data_handler.db.crud import InitializerDBConnector
from shared.constants import TOKEN_SETTINGS
from shared.helpers import add_leading_zeros
from shared.loan_entity import LoanEntity
from shared.state import State
from shared.types import InterestRateModels, Portfolio, TokenValues

logger = logging.getLogger(__name__)

R_TOKENS: dict[str, str] = {
    "ETH": "0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e",
    "USDC": "0x03bcecd40212e9b91d92bbe25bb3643ad93f0d230d93237c675f46fac5187e8c",
    "USDT": "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21",
    "DAI": "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f",
    "wBTC": "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef",
}

ADDRESSES_TO_TOKENS: dict[str, str] = {
    "0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e": "ETH",
    "0x03bcecd40212e9b91d92bbe25bb3643ad93f0d230d93237c675f46fac5187e8c": "USDC",
    "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21": "USDT",
    "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f": "DAI",
    "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef": "wBTC",
    "0x01ef7f9f8bf01678dc6d27e2c26fb7e8eac3812a24752e6a1d6a49d153bec9f3": "ETH",
    "0x021d8d8519f5464ec63c6b9a80a5229c5ddeed57ecded4c8a9dfc34e31b49990": "USDC",
    "0x012b8185e237dd0340340faeb3351dbe53f8a42f5a9bf974ddf90ced56e301c7": "USDT",
    "0x07eeed99c095f83716e465e2c52a3ec8f47b323041ddc4f97778ac0393b7f358": "DAI",
    "0x02614c784267d2026042ab98588f90efbffaade8982567e93530db4ed41201cf": "wBTC",
    # JediSwap pools.
    "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138": "JediSwap: DAI/ETH Pool",
    "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b": "JediSwap: DAI/USDC Pool",
    "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767": "JediSwap: DAI/USDT Pool",
    "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a": "JediSwap: ETH/USDC Pool",
    "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6": "JediSwap: ETH/USDT Pool",
    "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b":
    "JediSwap: USDC/USDT Pool",
    "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c": "JediSwap: WBTC/ETH Pool",
    "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8":
    "JediSwap: WBTC/USDC Pool",
    "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0":
    "JediSwap: WBTC/USDT Pool",
    # MySwap pools.
    "0x07c662b10f409d7a0a69c8da79b397fd91187ca5f6230ed30effef2dceddc5b3": "mySwap: DAI/ETH Pool",
    "0x0611e8f4f3badf1737b9e8f0ca77dd2f6b46a1d33ce4eed951c6b18ac497d505": "mySwap: DAI/USDC Pool",
    "0x022b05f9396d2c48183f6deaf138a57522bcc8b35b67dee919f76403d1783136": "mySwap: ETH/USDC Pool",
    "0x041f9a1e9a4d924273f5a5c0c138d52d66d2e6a8bee17412c6b0f48fe059ae04": "mySwap: ETH/USDT Pool",
    "0x01ea237607b7d9d2e9997aa373795929807552503683e35d8739f4dc46652de1": "mySwap: USDC/USDT Pool",
    "0x025b392609604c75d62dde3d6ae98e124a31b49123b8366d7ce0066ccb94f696": "mySwap: WBTC/USDC Pool",
    # TODO: Non-Hashstack specific tokens. This mapping duplicates information
    # from `TOKEN_SETTINGS`.
    "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3": "DAI",
    "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": "ETH",
    "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": "USDC",
    "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8": "USDT",
    "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac": "wBTC",
}


@dataclasses.dataclass
class HashstackV1SpecificTokenSettings:
    """
    Token settings specific to Hashstack V1, with neutral collateral and debt factors.
    """
    # These are set to neutral values because Hashstack V1 doesn't use collateral factors.
    collateral_factor: decimal.Decimal
    # These are set to neutral values because Hashstack V1 doesn't use debt factors.
    debt_factor: decimal.Decimal


@dataclasses.dataclass
class CustomTokenSettings(HashstackV1SpecificTokenSettings, TokenSettings):
    """
    Custom token settings for Hashstack V1, extending specific and general token settings.
    """
    pass


HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "JediSwap: DAI/ETH Pool":
    TokenSettings(
        symbol="JediSwap: DAI/ETH Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
    ),
    "JediSwap: DAI/USDC Pool":
    TokenSettings(
        symbol="JediSwap: DAI/USDC Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
    ),
    "JediSwap: DAI/USDT Pool":
    TokenSettings(
        symbol="JediSwap: DAI/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
    ),
    "JediSwap: ETH/USDC Pool":
    TokenSettings(
        symbol="JediSwap: ETH/USDC Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    ),
    "JediSwap: ETH/USDT Pool":
    TokenSettings(
        symbol="JediSwap: ETH/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
    ),
    "JediSwap: USDC/USDT Pool":
    TokenSettings(
        symbol="JediSwap: USDC/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
    ),
    "JediSwap: WBTC/ETH Pool":
    TokenSettings(
        symbol="JediSwap: WBTC/ETH Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
    ),
    "JediSwap: WBTC/USDC Pool":
    TokenSettings(
        symbol="JediSwap: WBTC/USDC Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
    ),
    "JediSwap: WBTC/USDT Pool":
    TokenSettings(
        symbol="JediSwap: WBTC/USDT Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
    ),
    "mySwap: DAI/ETH Pool":
    TokenSettings(
        symbol="mySwap: DAI/ETH Pool",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x07c662b10f409d7a0a69c8da79b397fd91187ca5f6230ed30effef2dceddc5b3",
    ),
    "mySwap: DAI/USDC Pool":
    TokenSettings(
        symbol="mySwap: DAI/USDC Pool",
        decimal_factor=decimal.Decimal("1e12"),
        address="0x0611e8f4f3badf1737b9e8f0ca77dd2f6b46a1d33ce4eed951c6b18ac497d505",
    ),
    "mySwap: ETH/USDC Pool":
    TokenSettings(
        symbol="mySwap: ETH/USDC Pool",
        decimal_factor=decimal.Decimal("1e12"),
        address="0x022b05f9396d2c48183f6deaf138a57522bcc8b35b67dee919f76403d1783136",
    ),
    "mySwap: ETH/USDT Pool":
    TokenSettings(
        symbol="mySwap: ETH/USDT Pool",
        decimal_factor=decimal.Decimal("1e12"),
        address="0x041f9a1e9a4d924273f5a5c0c138d52d66d2e6a8bee17412c6b0f48fe059ae04",
    ),
    "mySwap: USDC/USDT Pool":
    TokenSettings(
        symbol="mySwap: USDC/USDT Pool",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x01ea237607b7d9d2e9997aa373795929807552503683e35d8739f4dc46652de1",
    ),
    "mySwap: WBTC/USDC Pool":
    TokenSettings(
        symbol="mySwap: WBTC/USDC Pool",
        decimal_factor=decimal.Decimal("1e7"),
        address="0x025b392609604c75d62dde3d6ae98e124a31b49123b8366d7ce0066ccb94f696",
    ),
}
HASHSTACK_V1_SPECIFIC_TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "ETH":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "wBTC":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDC":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "DAI":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    "USDT":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"), debt_factor=decimal.Decimal("1")
    ),
    # TODO: Add wstETH.
    "wstETH":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    # TODO: Add LORDS.
    "LORDS":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    # TODO: Add STRK.
    "STRK":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: DAI/ETH Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: DAI/USDC Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: DAI/USDT Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: ETH/USDC Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: ETH/USDT Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: USDC/USDT Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: WBTC/ETH Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: WBTC/USDC Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "JediSwap: WBTC/USDT Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: DAI/ETH Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: DAI/USDC Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: ETH/USDC Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: ETH/USDT Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: USDC/USDT Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
    "mySwap: WBTC/USDC Pool":
    HashstackV1SpecificTokenSettings(
        collateral_factor=decimal.Decimal("1"),
        debt_factor=decimal.Decimal("1"),
    ),
}
TOKEN_SETTINGS: dict[str, CustomTokenSettings] = {
    token:
    CustomTokenSettings(
        symbol=token_settings.symbol,
        decimal_factor=token_settings.decimal_factor,
        address=token_settings.address,
        collateral_factor=HASHSTACK_V1_SPECIFIC_TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=HASHSTACK_V1_SPECIFIC_TOKEN_SETTINGS[token].debt_factor,
    )
    for token, token_settings in (TOKEN_SETTINGS | HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS).items()
}

# Keys are values of the "key_name" column in the database, values are the respective method names.
EVENTS_METHODS_MAPPING: dict[str, str] = {
    "new_loan": "process_new_loan_event",
    "collateral_added": "process_collateral_added_event",
    "loan_spent": "process_loan_spent_event",
    "loan_transferred": "process_loan_transferred_event",
    "loan_repaid": "process_loan_repaid_event",
    "updated_supply_token_price": "process_updated_supply_token_price_event",
    "updated_debt_token_price": "process_updated_debt_token_price_event",
}

MAX_ROUNDING_ERRORS: TokenValues = MAX_ROUNDING_ERRORS
# TODO: The additional tokens are not allowed in `TokenValues`, fix this.
MAX_ROUNDING_ERRORS.values.update(
    {token: decimal.Decimal("0.5e13")
     for token in HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS}
)


class HashstackV1Portfolio(Portfolio):
    """A class that describes holdings of tokens of Hashstack users."""

    MAX_ROUNDING_ERRORS: TokenValues = MAX_ROUNDING_ERRORS

    def __init__(self) -> None:
        super().__init__()
        self.values.update(
            {token: decimal.Decimal("0")
             for token in HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS}
        )


class HashstackV1InterestRateModels(TokenValues):
    """
    A class that describes the state of the interest rate indices which help transform face amounts into raw amounts.
    Raw amount is the amount that would have been accumulated into the face amount if it were deposited at genesis.
    """

    def __init__(self) -> None:
        super().__init__(init_value=decimal.Decimal("1"))
        self.values.update(
            {token: decimal.Decimal("1")
             for token in HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS}
        )


class HashstackV1LoanEntity(LoanEntity):
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
        self.original_collateral: HashstackV1Portfolio = HashstackV1Portfolio()
        self.borrowed_collateral: HashstackV1Portfolio = HashstackV1Portfolio()
        self.collateral: HashstackV1Portfolio = HashstackV1Portfolio()
        self.debt: HashstackV1Portfolio = HashstackV1Portfolio()

    def compute_health_factor(
        self,
        standardized: bool,
        collateral_interest_rate_models: Optional[InterestRateModels] = None,
        debt_interest_rate_models: Optional[InterestRateModels] = None,
        prices: Optional[TokenValues] = None,
        collateral_usd: Optional[decimal.Decimal] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        if collateral_usd is None:
            collateral_usd = self.compute_collateral_usd(
                risk_adjusted=False,
                collateral_interest_rate_models=collateral_interest_rate_models,
                prices=prices,
            )
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
            )
        if standardized:
            # Denominator is the value of (risk-adjusted) collateral at which the loan entity can be liquidated.
            # TODO: Does this parameter still hold?
            denominator = decimal.Decimal("1.04") * debt_usd
        else:
            denominator = debt_usd
        if denominator == decimal.Decimal("0"):
            # TODO: Assumes collateral is positive.
            return decimal.Decimal("Inf")
        return collateral_usd / denominator

    def compute_debt_to_be_liquidated(
        self,
        debt_interest_rate_models: Optional[InterestRateModels] = None,
        prices: Optional[TokenValues] = None,
        debt_usd: Optional[decimal.Decimal] = None,
    ) -> decimal.Decimal:
        # TODO: Has the liquidation mechanism changed?
        if debt_usd is None:
            debt_usd = self.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=debt_interest_rate_models,
                prices=prices,
            )
        return debt_usd


class HashstackV1State(State):
    """
    A class that describes the state of all Hashstack V1 loan entities. It implements a method for correct processing
    of every relevant event. Hashstack V1 events always contain the final state of the loan entity's collateral and
    debt, thus we always rewrite the balances whenever they are updated.
    """

    ADDRESSES_TO_TOKENS: dict[str, str] = ADDRESSES_TO_TOKENS
    EVENTS_METHODS_MAPPING: dict[str, str] = EVENTS_METHODS_MAPPING

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=HashstackV1LoanEntity,
            verbose_user=verbose_user,
        )
        # Initialize the DB connector.
        self.db_connector = InitializerDBConnector()
        # These models reflect the interest rates at which users lend/stake funds.
        self.collateral_interest_rate_models: HashstackV1InterestRateModels = (
            HashstackV1InterestRateModels()
        )
        # These models reflect the interest rates at which users borrow funds.
        self.debt_interest_rate_models: HashstackV1InterestRateModels = (
            HashstackV1InterestRateModels()
        )

    # TODO: There appears to be some overlap with HashstackV0State. Can we simplify the code?
    # TODO: Reduce most of the events processing to `rewrite_original_collateral`, `rewrite_borrowed_collateral`, and
    # `rewrite_debt`?

    def process_updated_supply_token_price_event(self, event: pd.Series) -> None:
        """
        Example of transaction: https://starkscan.co/tx/0x028050442976bffce8d858a759f195e206c2d4424f93479b83665094236712f8#events
        data column structure:
           - 0 - token_supply # doesn't work for us
           - 1 - underlying_asset # is applicable for `get_symbol`
           - 2 - total_supply
           - 4 - total_assets
           - 6 - timestamp
        :param event: pd.Series with event data
        :return: None
        """
        token = get_symbol(event["data"][1])
        # Convert total_supply and total_assets from hex to Decimal
        total_supply = decimal.Decimal(str(int(event["data"][2], base=16)))
        total_assets = decimal.Decimal(str(int(event["data"][4], base=16)))

        # Calculate the cumulative interest rate
        cumulative_interest_rate = total_assets / total_supply

        # Store the interest rate in the collateral_interest_rate_models attribute

        self.collateral_interest_rate_models.values[token] = cumulative_interest_rate

    def process_updated_debt_token_price_event(self, event: pd.Series) -> None:
        """
        Example of transaction in starkscan: https://starkscan.co/event/0x0486fea45f212bba4600c959d3aca4108f442c10a3e2e4d2e97ccd8f2e59a834_5
        Data structure of `event[data]`:
            - debt_token: 0
            - underlying_asset: 1
            - total_supply: 2
            - total_debt: 4
            - timestamp: 6
        :param event: pd.Series with event data
        :return: None
        """
        token = get_symbol(event["data"][1])
        # Convert total_supply and total_assets from hex to Decimal
        total_supply = decimal.Decimal(str(int(event["data"][2], base=16)))
        total_debt = decimal.Decimal(str(int(event["data"][4], base=16)))

        # Calculate the cumulative interest rate
        if total_debt == decimal.Decimal("0") or total_supply == decimal.Decimal("0"):
            cumulative_interest_rate = decimal.Decimal("0")
        else:
            cumulative_interest_rate = total_debt / total_supply

        # Store the interest rate in the collateral_interest_rate_models attribute
        self.debt_interest_rate_models.values[token] = cumulative_interest_rate

    def process_new_loan_event(self, event: pd.Series) -> None:
        """
        Process a new loan event and initialize a new loan entity for the user.
        """
        # The order of the values in the `data` column is: [`loan_record`] `loan_id`, `borrower`, `market`, `amount`,
        # ``, `current_market`, `current_amount`, ``, `state`, `l3_integration`, `l3_category`, `created_at`,
        # [`collateral`] `loan_id`, `collateral_token`, `amount`, ``, `created_at`, [`timestamp`] `timestamp`.
        # Example:
        # https://starkscan.co/event/0x00085b80dbb6c3cb161bb2b73ebc8c3b3b806395fc5c9a0f110ae2a1fa04a578_9.
        loan_id = int(event["data"][0], base=16)
        collateral_loan_id = int(event["data"][12], base=16)
        assert loan_id == collateral_loan_id
        user = event["data"][1]

        debt_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(event["data"][2])]
        debt_face_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        borrowed_collateral_token = get_symbol(add_leading_zeros(event["data"][5]))
        borrowed_collateral_face_amount = decimal.Decimal(str(int(event["data"][6], base=16)))
        original_collateral_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(event["data"][13])]
        original_collateral_face_amount = decimal.Decimal(str(int(event["data"][14], base=16)))

        self.loan_entities[loan_id] = HashstackV1LoanEntity(user=user)
        # TODO: Make it possible to initialize `HashstackV1Portfolio`` with some
        # token amount directly.
        original_collateral = HashstackV1Portfolio()
        original_collateral.values[original_collateral_token] = (original_collateral_face_amount)
        self.loan_entities[loan_id].original_collateral = original_collateral
        # add additional info block and timestamp
        self.loan_entities[loan_id].extra_info.block = event["block_number"]
        self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]

        borrowed_collateral = HashstackV1Portfolio()
        borrowed_collateral.values[borrowed_collateral_token] = (borrowed_collateral_face_amount)
        self.loan_entities[loan_id].borrowed_collateral = borrowed_collateral
        # TODO: Make it easier to sum 2 `HashstackV1Portfolio` instances.
        self.loan_entities[loan_id].collateral.values = {
            token: (
                self.loan_entities[loan_id].original_collateral.values[token] +
                self.loan_entities[loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        debt = HashstackV1Portfolio()
        debt.values[debt_token] = debt_face_amount
        self.loan_entities[loan_id].debt = debt
        loan_entity = self.loan_entities[loan_id]

        self.db_connector.save_debt_category(
            user_id=user,
            loan_id=loan_id,
            debt_category=loan_entity.debt_category,
            collateral=loan_entity.collateral.values,
            debt=loan_entity.debt.values,
            original_collateral=loan_entity.original_collateral.values,
            borrowed_collateral=loan_entity.borrowed_collateral.values,
            version=1,
        )

        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, face amount = {} of token = {} was borrowed against original collateral face "
                "amount = {} of token = {} and borrowed collateral face amount = {} of token = {}.".
                format(
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

    def process_collateral_added_event(self, event: pd.Series) -> None:
        """
        Process the collateral added event, adjusting the loan entity's collateral balances.
        """
        # The order of the values in the `data` column is: [`collateral_record`] `loan_id`, `collateral_token`,
        # `amount`, ``, `created_at`, [`amount_added`] `amount_added`, ``, [`timestamp`] `timestamp`.
        # Example:
        # https://starkscan.co/event/0x027b7e40273848af37e092eaec38311ac1d2e6c3fc2724020736e9f322b6fcf7_0.
        loan_id = int(event["data"][0], base=16)

        original_collateral_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(event["data"][1])]
        original_collateral_face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))

        original_collateral = HashstackV1Portfolio()
        original_collateral.values[original_collateral_token] = (original_collateral_face_amount)
        self.loan_entities[loan_id].original_collateral = original_collateral
        self.loan_entities[loan_id].collateral.values = {
            token: (
                self.loan_entities[loan_id].original_collateral.values[token] +
                self.loan_entities[loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        if self.loan_entities[loan_id].user == self.verbose_user:
            logging.info(
                "In block number = {}, collateral was added, resulting in collateral of face amount = {} of token = "
                "{}.".format(
                    event["block_number"],
                    original_collateral_face_amount,
                    original_collateral_token,
                )
            )

    def process_loan_spent_event(self, event: pd.Series) -> None:
        """
        Process the loan spent event, updating the loan entity with new debt and collateral details.
        """
        # The order of the values in the `data` column is: [`old_loan_record`] `loan_id`, `borrower`, `market`,
        # `amount`, ``, `current_market`, `current_amount`, ``, `state`, `l3_integration`, `l3_category`, `created_at`,
        # [`new_loan_record`] `loan_id`, `borrower`, `market`, `amount`, ``, `current_market`, `current_amount`, ``,
        # `state`, `l3_integration`, `l3_category`, `created_at`, [`timestamp`] `timestamp`.
        # Example:
        # https://starkscan.co/event/0x0051f75ef1e08f70d1c8efe7866384d026aa0ca092ded8bd1c903aac0478b990_25.
        old_loan_id = int(event["data"][0], base=16)
        old_user = event["data"][1]
        assert self.loan_entities[old_loan_id].user == old_user
        new_loan_id = int(event["data"][12], base=16)
        new_user = event["data"][13]
        # TODO: Does this always have to hold?
        assert new_loan_id == old_loan_id
        # TODO: Does this always have to hold?
        assert new_user == old_user

        new_debt_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(event["data"][14])]
        new_debt_face_amount = decimal.Decimal(str(int(event["data"][15], base=16)))
        new_borrowed_collateral_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(
            event["data"][17]
        )]
        new_borrowed_collateral_face_amount = decimal.Decimal(str(int(event["data"][18], base=16)))

        new_borrowed_collateral = HashstackV1Portfolio()
        new_borrowed_collateral.values[new_borrowed_collateral_token] = (
            new_borrowed_collateral_face_amount
        )
        self.loan_entities[new_loan_id].borrowed_collateral = new_borrowed_collateral
        self.loan_entities[new_loan_id].collateral.values = {
            token: (
                self.loan_entities[new_loan_id].original_collateral.values[token] +
                self.loan_entities[new_loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        new_debt = HashstackV1Portfolio()
        new_debt.values[new_debt_token] = new_debt_face_amount
        # Based on the documentation, it seems that it's only possible to spend the whole amount.
        assert self.loan_entities[old_loan_id].debt.values == new_debt.values
        self.loan_entities[new_loan_id].debt = new_debt
        # add additional info block and timestamp
        self.loan_entities[new_loan_id].extra_info.block = event["block_number"]
        self.loan_entities[new_loan_id].extra_info.timestamp = event["timestamp"]

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

    def process_loan_transferred_event(self, event: pd.Series) -> None:
        """
        Process the loan transferred event, updating the loan entity's user.
        """
        # The order of the values in the `data` column is: [`loan_id`] `loan_id`, [`sender`] `sender`, [`reciever`]
        # `reciever`, [`timestamp`] `timestamp`.
        # Example:
        # https://starkscan.co/event/0x028ea2b3cb9759214c7ea18e86a2d1b33a4bf3f87b4b0b4eb75919c9ab87a62e_5.
        loan_id = int(event["data"][0], base=16)
        old_user = event["data"][1]
        assert self.loan_entities[loan_id].user == old_user
        new_user = event["data"][2]
        self.loan_entities[loan_id].user = new_user
        # add additional info block and timestamp
        self.loan_entities[loan_id].extra_info.block = event["block_number"]
        self.loan_entities[loan_id].extra_info.timestamp = event["timestamp"]

        if self.verbose_user in {old_user, self.loan_entities[loan_id].user}:
            logging.info(
                "In block number = {}, loan was transferred from user = {} to user = {}.".format(
                    event["block_number"],
                    old_user,
                    new_user,
                )
            )

    def process_loan_repaid_event(self, event: pd.Series) -> None:
        """
        Process the loan repaid event and update the relevant loan entity details.
        """
        # The order of the values in the `data` column is: [`loan_record`] `loan_id`, `borrower`, `market`, `amount`,
        # ``, `current_market`, `current_amount`, ``, `state`, `l3_integration`, `l3_category`, `created_at`,
        # [`new_loan_record`] `loan_id`, `borrower`, `market`, `amount`, ``, `current_market`, `current_amount`, ``,
        # `state`, `l3_integration`, `l3_category`, `created_at`, [`collateral_record`] `loan_id`, `collateral_token`,
        # `amount`, ``, `created_at`, [`totalUserDebt`] `totalUserDebt`, [`deficit`] `deficit`, [`timestamp`]
        # `timestamp`.
        # Example:
        # https://starkscan.co/event/0x0069ff177c728aae4248ba8625322f75f0c5df918215f9e5dee10fe22c1fa26c_53.
        old_loan_id = int(event["data"][0], base=16)
        old_user = event["data"][1]
        assert self.loan_entities[old_loan_id].user == old_user
        new_loan_id = int(event["data"][12], base=16)
        new_user = event["data"][13]
        # TODO: Does this always have to hold?
        assert new_loan_id == old_loan_id
        # TODO: Does this always have to hold?
        assert new_user == old_user
        new_collateral_loan_id = int(event["data"][24], base=16)
        assert new_loan_id == new_collateral_loan_id

        new_debt_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(event["data"][14])]
        new_debt_face_amount = decimal.Decimal(str(int(event["data"][15], base=16)))
        new_borrowed_collateral_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(
            event["data"][17]
        )]
        new_borrowed_collateral_face_amount = decimal.Decimal(str(int(event["data"][18], base=16)))
        new_original_collateral_token = self.ADDRESSES_TO_TOKENS[add_leading_zeros(
            event["data"][25]
        )]
        new_original_collateral_face_amount = decimal.Decimal(str(int(event["data"][26], base=16)))
        # Based on the documentation, it seems that it's only possible to repay the whole amount.
        assert new_debt_face_amount == decimal.Decimal("0")
        assert new_borrowed_collateral_face_amount == decimal.Decimal("0")
        assert new_original_collateral_face_amount == decimal.Decimal("0")

        new_original_collateral = HashstackV1Portfolio()
        new_original_collateral.values[new_original_collateral_token] = (
            new_original_collateral_face_amount
        )
        new_borrowed_collateral = HashstackV1Portfolio()
        new_borrowed_collateral.values[new_borrowed_collateral_token] = (
            new_borrowed_collateral_face_amount
        )
        self.loan_entities[new_loan_id].original_collateral = new_original_collateral
        self.loan_entities[new_loan_id].borrowed_collateral = new_borrowed_collateral
        # add additional info block and timestamp
        self.loan_entities[new_loan_id].extra_info.block = event["block_number"]
        self.loan_entities[new_loan_id].extra_info.timestamp = event["timestamp"]

        self.loan_entities[new_loan_id].collateral.values = {
            token: (
                self.loan_entities[new_loan_id].original_collateral.values[token] +
                self.loan_entities[new_loan_id].borrowed_collateral.values[token]
            )
            for token in TOKEN_SETTINGS
        }
        new_debt = HashstackV1Portfolio()
        new_debt.values[new_debt_token] = new_debt_face_amount
        self.loan_entities[new_loan_id].debt = new_debt
        # add additional info block and timestamp
        self.loan_entities[new_loan_id].extra_info.block = event["block_number"]
        self.loan_entities[new_loan_id].extra_info.timestamp = event["timestamp"]

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

    def compute_liquidable_debt_at_price(
        self,
        prices: TokenValues,
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        debt_token: str,
    ) -> decimal.Decimal:
        changed_prices = copy.deepcopy(prices)
        changed_prices.values[collateral_token] = collateral_token_price
        max_liquidated_amount = decimal.Decimal("0")
        for loan_entity in self.loan_entities.values():
            # Filter out users who borrowed the token of interest.
            debt_tokens = {
                token
                for token, token_amount in loan_entity.debt.values.items()
                if decimal.Decimal(token_amount) > decimal.Decimal("0")
            }
            if debt_token not in debt_tokens:
                continue

            # Filter out users with health factor below 1.
            debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=self.debt_interest_rate_models,
                prices=changed_prices,
            )
            health_factor = loan_entity.compute_health_factor(
                standardized=False,
                collateral_interest_rate_models=self.collateral_interest_rate_models,
                prices=changed_prices,
                debt_usd=debt_usd,
            )
            # TODO: Does this parameter still hold?
            if health_factor >= decimal.Decimal("1.04"):
                continue

            # Find out how much of the `debt_token` will be liquidated.
            max_liquidated_amount += loan_entity.compute_debt_to_be_liquidated(debt_usd=debt_usd)
        return max_liquidated_amount

    def compute_number_of_active_users(self) -> int:
        """
        Calculate the number of unique users with active collateral or debt.
        """
        unique_active_users = {
            loan_entity.user
            for loan_entity in self.loan_entities.values()
            if loan_entity.has_collateral() or loan_entity.has_debt()
        }
        return len(unique_active_users)

    def compute_number_of_active_borrowers(self) -> int:
        """
        Calculate the number of unique users with active debt.
        """
        unique_active_borrowers = {
            loan_entity.user
            for loan_entity in self.loan_entities.values() if loan_entity.has_debt()
        }
        return len(unique_active_borrowers)
