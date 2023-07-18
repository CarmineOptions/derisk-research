from typing import Dict
import asyncio
import copy
import decimal

import pandas
import streamlit as st

import classes
import swap_liquidity


# Source: Starkscan, e.g.
# https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
TOKEN_DECIMAL_FACTORS = {
    "ETH": decimal.Decimal("1e18"),
    "wBTC": decimal.Decimal("1e8"),
    "USDC": decimal.Decimal("1e6"),
    "DAI": decimal.Decimal("1e18"),
    "USDT": decimal.Decimal("1e6"),
}


# Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
COLLATERAL_FACTORS = {
    "ETH": decimal.Decimal("0.80"),
    "wBTC": decimal.Decimal("0.70"),
    "USDC": decimal.Decimal("0.80"),
    "DAI": decimal.Decimal("0.70"),
    "USDT": decimal.Decimal("0.70"),
}


# Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
LIQUIDATION_BONUSES = {
    "ETH": decimal.Decimal("0.10"),
    "wBTC": decimal.Decimal("0.15"),
    "USDC": decimal.Decimal("0.10"),
    "DAI": decimal.Decimal("0.10"),
    "USDT": decimal.Decimal("0.10"),
}


def compute_risk_adjusted_collateral_usd(
    user_state: classes.UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        token_state.collateral_enabled
        * token_state.deposit
        * COLLATERAL_FACTORS[token]
        * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[token]
        for token, token_state in user_state.token_states.items()
        if not token_state.z_token
    )


def compute_borrowings_usd(
    user_state: classes.UserState,
    prices: Dict[str, decimal.Decimal],
) -> decimal.Decimal:
    return sum(
        token_state.borrowings
        * prices[token]
        # TODO: perform the conversion using TOKEN_DECIMAL_FACTORS sooner (in `UserTokenState`?)?
        / TOKEN_DECIMAL_FACTORS[token]
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
        - collateral_token_collateral_factor * (1 + collateral_token_liquidation_bonus)
    )
    return numerator / denominator


def compute_max_liquidated_amount(
    state: classes.State,
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
            collateral_token_collateral_factor=COLLATERAL_FACTORS[collateral_token],
            collateral_token_liquidation_bonus=LIQUIDATION_BONUSES[collateral_token],
        )
    return liquidated_borrowings_amount


def decimal_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal):
    while start < stop:
        yield start
        start += step


def simulate_liquidations_under_absolute_price_change(
    prices: classes.Prices,
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
    state: classes.State,
    borrowings_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] = collateral_token_price
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, borrowings_token=borrowings_token
    )


def simulate_liquidations_under_price_change(
    prices: classes.Prices,
    collateral_token: str,
    collateral_token_price_multiplier: decimal.Decimal,
    state: classes.State,
    borrowings_token: str,
) -> decimal.Decimal:
    changed_prices = copy.deepcopy(prices.prices)
    changed_prices[collateral_token] *= collateral_token_price_multiplier
    return compute_max_liquidated_amount(
        state=state, prices=changed_prices, borrowings_token=borrowings_token
    )


def get_amm_supply_at_price(
        collateral_token: str,
        collateral_token_price: decimal.Decimal,
        borrowings_token: str,
    ) -> decimal.Decimal:
        return jediswap.get_pool(collateral_token, borrowings_token).supply_at_price(borrowings_token, collateral_token_price)


def update_graph_data():
    params = st.session_state["parameters"]

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
    data["max_borrowings_to_be_liquidated"] = data[
        "collateral_token_price"
    ].apply(
        lambda x: simulate_liquidations_under_absolute_price_change(
            prices=st.session_state.prices,
            collateral_token=params["COLLATERAL_TOKEN"],
            collateral_token_price=x,
            state=st.session_state.state,
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
    jediswap = swap_liquidity.SwapAmm('JediSwap')
    jediswap.add_pool('ETH', 'USDC', '0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a')
    asyncio.run(jediswap.get_balance())

    data['amm_borrowings_token_supply'] = \
        data['collateral_token_price'].apply(
            lambda x: get_amm_supply_at_price(
                collateral_token = COLLATERAL_TOKEN,
                collateral_token_price = x,
                borrowings_token = BORROWINGS_TOKEN,
            )
        )

    st.session_state["data"] = data
