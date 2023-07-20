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
          from_address='{constants.Protocol.ZKLEND.value}'
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


def load_graph_data():
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
    data["max_borrowings_to_be_liquidated"] = data["collateral_token_price"].apply(
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
    jediswap = SwapAmm("JediSwap")
    jediswap.add_pool(
        "ETH",
        "USDC",
        "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    )
    asyncio.run(jediswap.get_balance())

    data["amm_borrowings_token_supply"] = data["collateral_token_price"].apply(
        lambda x: get_amm_supply_at_price(
            collateral_token=st.session_state["parameters"]["COLLATERAL_TOKEN"],
            collateral_token_price=x,
            borrowings_token=st.session_state["parameters"]["BORROWINGS_TOKEN"],
            amm=jediswap,
        )
    )

    st.session_state["data"] = data


def bench(msg, start):
    print(f"{msg} --- {round(time.time() - start, 2)}s")


@st.cache_data(ttl=10)
def load_state():
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
    load_graph_data()
    bench("processed graph data", t3)
    bench("full state update", t0)
