from typing import Dict
import asyncio
import collections
import copy
import decimal

import pandas
import numpy
import streamlit

import src.constants
import src.swap_liquidity


# TODO: convert numbers/amounts (divide by sth)
# TODO: remove irrelevant variables (in events)
# TODO: add self.user to UserState and UserTokenState?
# TODO: add logs
class AccumulatorState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.lending_accumulator: decimal.Decimal = decimal.Decimal("1e27")
        self.debt_accumulator: decimal.Decimal = decimal.Decimal("1e27")

    def accumulators_sync(
        self, lending_accumulator: decimal.Decimal, debt_accumulator: decimal.Decimal
    ):
        self.lending_accumulator = lending_accumulator / \
            decimal.Decimal("1e27")
        self.debt_accumulator = debt_accumulator / decimal.Decimal("1e27")


class UserTokenState:
    """
    TODO

    We are making a simplifying assumption that when collateral is enabled, all
    deposits of the given token are considered as collateral.
    """

    # TODO: make it token-dependent (advanced solution: fetch token prices in $ -> round each token's
    #   balance e.g. to the nearest cent)
    MAX_ROUNDING_ERRORS = {
        "ETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
        "wBTC": decimal.Decimal("1e2"),
        "USDC": decimal.Decimal("1e4"),
        "DAI": decimal.Decimal("1e16"),
        "USDT": decimal.Decimal("1e4"),
    }

    def __init__(self, token: str) -> None:
        self.token: str = token
        self.deposit: decimal.Decimal = decimal.Decimal("0")
        self.collateral_enabled: bool = False
        self.borrowings: decimal.Decimal = decimal.Decimal("0")
        self.z_token: bool = token[0] == "z"

    def update_borrowings(self, raw_amount: decimal.Decimal):
        self.borrowings += raw_amount
        if (
            -self.MAX_ROUNDING_ERRORS[self.token]
            < self.borrowings
            < self.MAX_ROUNDING_ERRORS[self.token]
        ):
            self.borrowings = decimal.Decimal("0")

    def update_deposit(self, raw_amount: decimal.Decimal):
        self.deposit += raw_amount
        if (
            -self.MAX_ROUNDING_ERRORS[self.token]
            < self.deposit
            < self.MAX_ROUNDING_ERRORS[self.token]
        ):
            self.deposit = decimal.Decimal("0")


class UserState:
    """
    TODO
    """

    def __init__(self) -> None:
        self.token_states: Dict[str, UserTokenState] = {
            "ETH": UserTokenState("ETH"),
            "wBTC": UserTokenState("wBTC"),
            "USDC": UserTokenState("USDC"),
            "DAI": UserTokenState("DAI"),
            "USDT": UserTokenState("USDT"),
            "zETH": UserTokenState("zETH"),
            "zWBTC": UserTokenState("zWBTC"),
            "zUSDC": UserTokenState("zUSDC"),
            "zDAI": UserTokenState("zDAI"),
            "zUSDT": UserTokenState("zUSDT"),
        }
        # TODO: implement healt_factor
        # TODO: use decimal
        self.health_factor: float = 1.0  # TODO: is this a good default value??

    def deposit(self, token: str, raw_amount: decimal.Decimal):
        self.token_states[token].update_deposit(raw_amount)

    def withdrawal(self, token: str, raw_amount: decimal.Decimal):
        self.token_states[token].update_deposit(-raw_amount)

    def collateral_enabled(self, token: str):
        self.token_states[token].collateral_enabled = True

    def collateral_disabled(self, token: str):
        self.token_states[token].collateral_enabled = False

    def borrowing(
        self, token: str, raw_amount: decimal.Decimal, face_amount: decimal.Decimal
    ):
        self.token_states[token].update_borrowings(raw_amount)

    def repayment(
        self, token: str, raw_amount: decimal.Decimal, face_amount: decimal.Decimal
    ):
        self.token_states[token].update_borrowings(-raw_amount)

    def liquidation(
        self,
        debt_token: str,
        debt_raw_amount: decimal.Decimal,
        debt_face_amount: decimal.Decimal,
        collateral_token: decimal.Decimal,
        collateral_raw_amount: decimal.Decimal,
    ):
        self.token_states[debt_token].update_borrowings(-debt_raw_amount)
        self.token_states[collateral_token].update_deposit(
            -collateral_raw_amount)


class State:
    """
    TODO
    """

    EVENTS_FUNCTIONS_MAPPING: Dict[str, str] = {
        "Deposit": "process_deposit_event",
        "Withdrawal": "process_withdrawal_event",
        "CollateralEnabled": "process_collateral_enabled_event",
        "CollateralDisabled": "process_collateral_disabled_event",
        "Borrowing": "process_borrowing_event",
        "Repayment": "process_repayment_event",
        "Liquidation": "process_liquidation_event",
        "AccumulatorsSync": "process_accumulators_sync_event",
        "Transfer": "process_transfer_event",
    }
    USER = "0x204c44e83f63803bcae77406aa749636d23d3c914e4aa9c84f89f45bad0f844"

    def __init__(self) -> None:
        self.user_states: collections.defaultdict = collections.defaultdict(
            UserState)
        self.accumulator_states: Dict[str, AccumulatorState] = {
            "ETH": AccumulatorState(),
            "wBTC": AccumulatorState(),
            "USDC": AccumulatorState(),
            "DAI": AccumulatorState(),
            "USDT": AccumulatorState(),
        }
        self.last_block_number = 0

    def update_block_number(self, block_number):
        if isinstance(block_number, (int, numpy.integer)):
            self.last_block_number = block_number

    def process_event(self, event: pandas.Series) -> None:
        name = event["key_name"]
        getattr(self, self.EVENTS_FUNCTIONS_MAPPING[name])(event=event)

    def process_deposit_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`, `face_amount`.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        # TODO: divide by something or store like this?
        # TODO: any better conversion to decimals?
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        # TODO: sanity checks/asserts?
        raw_amount = face_amount / \
            self.accumulator_states[token].lending_accumulator
        self.user_states[user].deposit(token=token, raw_amount=raw_amount)
        # TODO
        if user == self.USER:
            print("dep", token, raw_amount)

    def process_withdrawal_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`, `face_amount`.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        face_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = face_amount / \
            self.accumulator_states[token].lending_accumulator
        self.user_states[user].withdrawal(token=token, raw_amount=raw_amount)
        # TODO
        if user == self.USER:
            print("wit", token, raw_amount)

    def process_collateral_enabled_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        self.user_states[user].collateral_enabled(token=token)
        # TODO
        if user == self.USER:
            print("colena", token)

    def process_collateral_disabled_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        self.user_states[user].collateral_disabled(token=token)
        # TODO
        if user == self.USER:
            print("coldis", token)

    def process_borrowing_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `user`, `token`, `raw_amount`, `face_amount`.
        user = event["data"][0]
        token = src.constants.get_symbol(event["data"][1])
        raw_amount = decimal.Decimal(str(int(event["data"][2], base=16)))
        face_amount = decimal.Decimal(
            str(int(event["data"][3], base=16))
        )  # TODO: relevant?
        self.user_states[user].borrowing(
            token=token,
            raw_amount=raw_amount,
            face_amount=face_amount,
        )
        # TODO
        if user == self.USER:
            print("bor", token, raw_amount)

    def process_repayment_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `repayer`, `beneficiary`, `token`, `raw_amount`,
        # `face_amount`.
        repayer = event["data"][0]  # TODO: relevant?
        beneficiary = event["data"][1]
        token = src.constants.get_symbol(event["data"][2])
        raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        face_amount = decimal.Decimal(
            str(int(event["data"][4], base=16))
        )  # TODO: relevant?
        self.user_states[beneficiary].repayment(
            token=token,
            raw_amount=raw_amount,
            face_amount=face_amount,
        )
        # TODO
        if beneficiary == self.USER:
            print("rep", token, raw_amount)

    def process_liquidation_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `liquidator`, `user`, `debt_token`, `debt_raw_amount`,
        # `debt_face_amount`, `collateral_token`, `collateral_amount`.
        liquidator = event["data"][0]  # TODO: relevant?
        user = event["data"][1]
        debt_token = src.constants.get_symbol(event["data"][2])
        debt_raw_amount = decimal.Decimal(str(int(event["data"][3], base=16)))
        debt_face_amount = decimal.Decimal(
            str(int(event["data"][4], base=16))
        )  # TODO: relevant?
        collateral_token = src.constants.get_symbol(event["data"][5])
        collateral_amount = decimal.Decimal(
            str(int(event["data"][6], base=16)))
        collateral_raw_amount = (
            collateral_amount
            / self.accumulator_states[collateral_token].lending_accumulator
        )
        self.user_states[user].liquidation(
            debt_token=debt_token,
            debt_raw_amount=debt_raw_amount,
            debt_face_amount=debt_face_amount,
            collateral_token=collateral_token,
            collateral_raw_amount=collateral_raw_amount,
        )
        # TODO
        if user == self.USER:
            print(
                "liq",
                debt_token,
                debt_raw_amount,
                collateral_token,
                collateral_raw_amount,
            )

    def process_accumulators_sync_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `token`, `lending_accumulator`, `debt_accumulator`.
        token = src.constants.get_symbol(event["data"][0])
        lending_accumulator = decimal.Decimal(
            str(int(event["data"][1], base=16)))
        debt_accumulator = decimal.Decimal(str(int(event["data"][2], base=16)))
        self.accumulator_states[token].accumulators_sync(
            lending_accumulator=lending_accumulator,
            debt_accumulator=debt_accumulator,
        )

    def process_transfer_event(self, event: pandas.Series) -> None:
        # The order of the arguments is: `from_`, `to`, `value`.
        empty_address = "0x0"
        # token contract emitted this event
        ztoken = src.constants.get_symbol(event["from_address"])
        # zTokens share accumulator value with token
        token = src.constants.ztoken_to_token(ztoken)
        from_ = event["data"][0]
        to = event["data"][1]
        value = decimal.Decimal(str(int(event["data"][2], base=16)))
        raw_amount = value / self.accumulator_states[token].lending_accumulator

        # TODO
        if from_ == self.USER or to == self.USER:
            print("tra", token, ztoken, debt_raw_amount, raw_amount)

        if from_ != empty_address:
            self.user_states[from_].withdrawal(
                token=ztoken, raw_amount=raw_amount)
        if to != empty_address:
            self.user_states[to].deposit(token=ztoken, raw_amount=raw_amount)


def compute_risk_adjusted_collateral_usd(
    user_state: UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        token_state.collateral_enabled
        * token_state.deposit
        * src.constants.COLLATERAL_FACTORS[token]
        * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / src.constants.TOKEN_DECIMAL_FACTORS[token]
        for token, token_state in user_state.token_states.items()
        if not token_state.z_token
    )


def compute_borrowings_usd(
    user_state: UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        token_state.borrowings * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / src.constants.TOKEN_DECIMAL_FACTORS[token]
        for token, token_state in user_state.token_states.items()
        if not token_state.z_token
    )


def compute_health_factor(
    risk_adjusted_collateral_usd: decimal.Decimal,
    borrowings_usd: decimal.Decimal,
) -> decimal.Decimal:
    if borrowings_usd == decimal.Decimal("0"):
        # TODO: assumes collateral is positive
        return decimal.Decimal("Inf")

    health_factor = risk_adjusted_collateral_usd / borrowings_usd
    # TODO: enable?
    #     if health_factor < decimal.Decimal('0.9'):
    #         print(f'Suspiciously low health factor = {health_factor} of user = {user}, investigate.')
    # TODO: too many loans eligible for liquidation?
    #     elif health_factor < decimal.Decimal('1'):
    #         print(f'Health factor = {health_factor} of user = {user} eligible for liquidation.')
    return health_factor


# TODO
# TODO: compute_health_factor, etc. should be methods of class UserState
def compute_borrowings_to_be_liquidated(
    risk_adjusted_collateral_usd: decimal.Decimal,
    borrowings_usd: decimal.Decimal,
    borrowings_token_price: decimal.Decimal,
    collateral_token_collateral_factor: decimal.Decimal,
    collateral_token_liquidation_bonus: decimal.Decimal,
) -> decimal.Decimal:
    # TODO: commit the derivation of the formula in a document?
    numerator = borrowings_usd - risk_adjusted_collateral_usd
    denominator = borrowings_token_price * (
        1
        - collateral_token_collateral_factor *
        (1 + collateral_token_liquidation_bonus)
    )
    return numerator / denominator


def compute_max_liquidated_amount(
    state: State,
    prices: Dict[str, decimal.Decimal],
    borrowings_token: str,
) -> decimal.Decimal:
    liquidated_borrowings_amount = decimal.Decimal("0")
    for user, user_state in state.user_states.items():
        # TODO: do this?
        # Filter out users who borrowed the token of interest.
        borrowings_tokens = {
            token_state.token
            for token_state in user_state.token_states.values()
            if token_state.borrowings > decimal.Decimal("0")
        }
        if not borrowings_token in borrowings_tokens:
            continue

        # Filter out users with health below 1.
        risk_adjusted_collateral_usd = compute_risk_adjusted_collateral_usd(
            user_state=user_state,
            prices=prices,
        )
        borrowings_usd = compute_borrowings_usd(
            user_state=user_state,
            prices=prices,
        )
        health_factor = compute_health_factor(
            risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
            borrowings_usd=borrowings_usd,
        )
        # TODO
        if health_factor >= decimal.Decimal("1") or health_factor <= decimal.Decimal(
            "0"
        ):
            #         if health_factor >= decimal.Decimal('1'):
            continue

        # TODO: find out how much of the borrowings_token will be liquidated
        collateral_tokens = {
            token_state.token
            for token_state in user_state.token_states.values()
            if token_state.deposit * token_state.collateral_enabled
            != decimal.Decimal("0")
        }
        # TODO: choose the most optimal collateral_token to be liquidated .. or is the liquidator indifferent?
        #         print(user, collateral_tokens, health_factor, borrowings_usd, risk_adjusted_collateral_usd)
        collateral_token = list(collateral_tokens)[0]
        liquidated_borrowings_amount += compute_borrowings_to_be_liquidated(
            risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
            borrowings_usd=borrowings_usd,
            borrowings_token_price=prices[borrowings_token],
            collateral_token_collateral_factor=src.constants.COLLATERAL_FACTORS[
                collateral_token],
            collateral_token_liquidation_bonus=src.constants.LIQUIDATION_BONUSES[
                collateral_token],
        )
    return liquidated_borrowings_amount


# TODO: this function is general for all protocols
def decimal_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal):
    while start < stop:
        yield start
        start += step


def simulate_liquidations_under_absolute_price_change(
    prices: src.swap_liquidity.Prices,
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
    state: State,
    borrowings_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] = collateral_token_price
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, borrowings_token=borrowings_token
    )


def simulate_liquidations_under_price_change(
    prices: src.swap_liquidity.Prices,
    collateral_token: str,
    collateral_token_price_multiplier: decimal.Decimal,
    state: State,
    borrowings_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] *= collateral_token_price_multiplier
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, borrowings_token=borrowings_token
    )


# TODO: this function is general for all protocols
def get_amm_supply_at_price(
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
    borrowings_token: str,
    amm: src.swap_liquidity.SwapAmm,
) -> decimal.Decimal:
    return amm.get_pool(collateral_token, borrowings_token).supply_at_price(
        borrowings_token, collateral_token_price
    )


def update_graph_data():
    params = streamlit.session_state["parameters"]

    data = pandas.DataFrame(
        {
            "collateral_token_price": [
                x
                for x in decimal_range(
                    # TODO: make it dependent on the collateral token .. use prices.prices[COLLATERAL_TOKEN]
                    start=decimal.Decimal("1000"),
                    stop=decimal.Decimal("3000"),
                    # TODO: make it dependent on the collateral token
                    step=decimal.Decimal("50"),
                )
            ]
        },
    )
    # TOOD: needed?
    # data['collateral_token_price_multiplier'] = data['collateral_token_price_multiplier'].map(decimal.Decimal)
    data["max_borrowings_to_be_liquidated"] = data["collateral_token_price"].apply(
        lambda x: simulate_liquidations_under_absolute_price_change(
            prices=streamlit.session_state.prices,
            collateral_token=params["COLLATERAL_TOKEN"],
            collateral_token_price=x,
            state=streamlit.session_state.state,
            borrowings_token=params["BORROWINGS_TOKEN"],
        )
    )

    # TODO
    data["max_borrowings_to_be_liquidated_at_interval"] = (
        data["max_borrowings_to_be_liquidated"].diff().abs()
    )
    # TODO: drops also other NaN, if there are any
    data.dropna(inplace=True)

    # Setup the AMM.
    swap_amms = asyncio.run(src.swap_liquidity.SwapAmm().init())

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: get_amm_supply_at_price(
            collateral_token=streamlit.session_state["parameters"]["COLLATERAL_TOKEN"],
            collateral_token_price=x,
            borrowings_token=streamlit.session_state["parameters"]["BORROWINGS_TOKEN"],
            amm=swap_amms,
        )
    )

    streamlit.session_state["data"] = data


def compute_number_of_users(
    state: State,
) -> int:
    return sum(
        any(
            token_state.deposit > decimal.Decimal('0')
            or token_state.borrowings > decimal.Decimal('0')
            for token_state in user_state.token_states.values()
            if not token_state.z_token
        )
        for user_state in state.user_states.values()
    )


def compute_number_of_stakers(
    state: State,
) -> int:
    return sum(
        any(token_state.deposit > decimal.Decimal('0') for token_state in user_state.token_states.values() if not token_state.z_token)
        for user_state in state.user_states.values()
    )


def compute_number_of_borrowers(
    state: State,
) -> int:
    return sum(
        any(token_state.borrowings > decimal.Decimal('0') for token_state in user_state.token_states.values() if not token_state.z_token)
        for user_state in state.user_states.values()
    )


def compute_standardized_health_factor(
    risk_adjusted_collateral_usd: decimal.Decimal,
    borrowings_usd: decimal.Decimal,
) -> decimal.Decimal:
    # Compute the value of collateral at which the user/loan can be liquidated.
    collateral_usd_threshold = borrowings_usd
    if collateral_usd_threshold == decimal.Decimal("0"):
        # TODO: assumes collateral is positive
        return decimal.Decimal("Inf")
    return risk_adjusted_collateral_usd / collateral_usd_threshold
