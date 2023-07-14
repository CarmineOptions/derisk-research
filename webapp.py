import asyncio
import decimal
import time
import pandas
import streamlit as st
import plotly.express

import classes
from compute import (
    decimal_range,
    update_graph_data,
)
from get_data import get_events
from persistent_state import load_persistent_state

# SESSION STATE
if "parameters" not in st.session_state:
    st.session_state["parameters"] = {
        "COLLATERAL_TOKEN": "ETH",
        "BORROWINGS_TOKEN": "USDC",
        "COLLATERAL_TOKEN_PRICE_MULTIPLIER": decimal.Decimal("0.99"),
        "X_AXIS_DESC": "collateral_token_price_multiplier",
        "Y_AXIS_DESC": "max_borrowings_to_be_liquidated",
    }

if "data" not in st.session_state:
    st.session_state["data"] = pandas.DataFrame(
        {
            st.session_state.parameters["X_AXIS_DESC"]: [
                x
                for x in decimal_range(
                    start=decimal.Decimal("0.5"),
                    stop=decimal.Decimal("1.51"),
                    step=decimal.Decimal("0.01"),
                )
            ]
        },
    )

load_persistent_state()

if "latest_block" not in st.session_state:
    st.session_state["latest_block"] = 0
if "state" not in st.session_state:
    st.session_state["state"] = classes.State()


def bench(msg, start):
    print(f"{msg} {round(time.time() - start, 2)}s")


async def hide_message(msg):
    await asyncio.sleep(10)
    msg.empty()


def main():
    st.title("DeRisk")

    def update_state():
        print("Updating...")
        t0 = time.time()
        # get new events
        events = get_events()
        bench("got events in", t0)
        t1 = time.time()
        for _, event in events.iterrows():
            st.session_state.state.process_event(event=event)
        bench("updated state in", t1)
        t2 = time.time()
        update_graph_data()
        bench("updated graph data in", t2)
        bench("entire update took", t0)

    if st.button("Update"):
        with st.spinner("Processing..."):
            update_state()
        msg = st.success("Updated!")
        asyncio.run(hide_message(msg))

    if st.session_state.parameters["Y_AXIS_DESC"] in st.session_state.data:
        figure = plotly.express.bar(
            st.session_state.data,
            x=st.session_state.parameters["X_AXIS_DESC"],
            y=st.session_state.parameters["Y_AXIS_DESC"],
        )
        st.plotly_chart(figure)


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
