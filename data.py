import asyncio
import decimal
import time
import streamlit as st
import pandas
import math

from compute import (
    decimal_range,
    get_amm_supply_at_price,
    simulate_liquidations_under_absolute_price_change,
)

import constants
import db
from persistent_state import load_persistent_state
from swap_liquidity import SwapAmm


def get_events() -> pandas.DataFrame:
    latest_block = st.session_state.latest_block
    print("getting events from block", latest_block)
    # Establish the connection.
    connection = db.establish_connection()

    # Load all Zklend events.
    zklend_events = pandas.read_sql(
        sql=f"""
      SELECT
          *
      FROM
          starkscan_events
      WHERE
          from_address='{constants.Protocol.Nostra.value}'
      AND
          key_name IN ('Deposit', 'Withdrawal', 'CollateralEnabled', 'CollateralDisabled', 'Borrowing', 'Repayment', 'Liquidation', 'AccumulatorsSync')
      AND
          block_number>{latest_block}
      ORDER BY
          block_number, id ASC;
      """,
        con=connection,
    )
    # Close the connection.
    connection.close()
    zklend_events.set_index("id", inplace=True)
    lb = zklend_events["block_number"].max()
    if not math.isnan(lb):
        print("new latest block", lb)
        st.session_state.latest_block = lb
    return zklend_events


# TODO: move this somewhere
token_range_mapping = {
    "ETH": [
        x
        for x in decimal_range(
            # TODO: make it dependent on the collateral token .. use prices.prices[COLLATERAL_TOKEN]
            start=decimal.Decimal("0"),
            stop=decimal.Decimal("3000"),
            # TODO: make it dependent on the collateral token
            step=decimal.Decimal("50"),
        )
    ],
    "wBTC": [
        x
        for x in decimal_range(
            # TODO: make it dependent on the collateral token .. use prices.prices[COLLATERAL_TOKEN]
            start=decimal.Decimal("0"),
            stop=decimal.Decimal("40000"),
            # TODO: make it dependent on the collateral token
            step=decimal.Decimal("1000"),
        )
    ],
}


def load_graph_data(collateral_token, borrowings_token):
    data = pandas.DataFrame(
        {"collateral_token_price": token_range_mapping[collateral_token]},
    )
    # TOOD: needed?
    # data['collateral_token_price_multiplier'] = data['collateral_token_price_multiplier'].map(decimal.Decimal)
    data["max_borrowings_to_be_liquidated"] = data["collateral_token_price"].apply(
        lambda x: simulate_liquidations_under_absolute_price_change(
            prices=st.session_state.prices,
            collateral_token=collateral_token,
            collateral_token_price=x,
            state=st.session_state.state,
            borrowings_token=borrowings_token,
        )
    )

    # TODO
    data["max_borrowings_to_be_liquidated_at_interval"] = (
        data["max_borrowings_to_be_liquidated"].diff().abs()
    )
    # TODO: drops also other NaN, if there are any
    data.dropna(inplace=True)

    # Setup the AMM.
    jediswap = SwapAmm("JediSwap")
    jediswap.add_pool(
        "ETH",
        "USDC",
        "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    )
    jediswap.add_pool(
        "DAI",
        "ETH",
        "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
    )
    jediswap.add_pool(
        "ETH",
        "USDT",
        "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
    )
    jediswap.add_pool(
        "wBTC",
        "ETH",
        "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
    )
    jediswap.add_pool(
        "wBTC",
        "USDC",
        "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
    )
    jediswap.add_pool(
        "wBTC",
        "USDT",
        "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
    )
    jediswap.add_pool(
        "DAI",
        "wBTC",
        "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",
    )
    jediswap.add_pool(
        "DAI",
        "USDC",
        "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
    )
    jediswap.add_pool(
        "DAI",
        "USDT",
        "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
    )
    jediswap.add_pool(
        "USDC",
        "USDT",
        "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
    )
    asyncio.run(jediswap.get_balance())

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: get_amm_supply_at_price(
            collateral_token=collateral_token,
            collateral_token_price=x,
            borrowings_token=borrowings_token,
            amm=jediswap,
        )
    )

    st.session_state["data"] = data


def bench(msg, start):
    print(f"{msg} --- {round(time.time() - start, 2)}s")


def load_state(collateral_token, borrowings_token):
    print("Loading state for", collateral_token, borrowings_token)
    t0 = time.time()
    if "state" not in st.session_state and "latest_block" not in st.session_state:
        load_persistent_state()
        bench("loaded persistent state", t0)
    t1 = time.time()
    new_events = get_events()
    bench("got new events", t1)
    t2 = time.time()
    for _, event in new_events.iterrows():
        st.session_state["state"].process_event(event=event)
    bench("processed new events", t2)
    t3 = time.time()
    load_graph_data(collateral_token, borrowings_token)
    bench("processed graph data", t3)
    bench("full state update", t0)
