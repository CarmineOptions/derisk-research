import decimal
import time
import pandas
import streamlit as st
import plotly.express

import classes
from compute import (
    decimal_range,
    simulate_liquidations_under_price_change,
)
from get_data import get_events

# GLOBALS
COLLATERAL_TOKEN = "wBTC"
BORROWINGS_TOKEN = "USDC"
COLLATERAL_TOKEN_PRICE_MULTIPLIER = decimal.Decimal("0.99")
COLLATERAL_TOKEN = "ETH"
BORROWINGS_TOKEN = "USDC"
prices = classes.Prices()

# SESSION STATE
if "latest_block" not in st.session_state:
    st.session_state["latest_block"] = 0
    st.session_state["state"] = classes.State()
    st.session_state["data"] = pandas.DataFrame(
        {
            "collateral_token_price_multiplier": [
                x
                for x in decimal_range(
                    start=decimal.Decimal("0.5"),
                    stop=decimal.Decimal("1.51"),
                    step=decimal.Decimal("0.01"),
                )
            ]
        },
    )


def main():
    st.title("DeRisk by Carmine Finance")

    def update_state():
        start = time.time()
        # get new events
        events = get_events()
        for _, event in events.iterrows():
            st.session_state.state.process_event(event=event)
        # update prices
        st.session_state.data[
            "collateral_token_price_multiplier"
        ] = st.session_state.data["collateral_token_price_multiplier"].map(
            decimal.Decimal
        )
        st.session_state.data[
            "max_borrowings_to_be_liquidated"
        ] = st.session_state.data["collateral_token_price_multiplier"].apply(
            lambda x: simulate_liquidations_under_price_change(
                prices=prices,
                collateral_token=COLLATERAL_TOKEN,
                collateral_token_price_multiplier=x,
                state=st.session_state.state,
                borrowings_token=BORROWINGS_TOKEN,
            )
        )
        figure = plotly.express.bar(
            st.session_state.data,
            x="collateral_token_price_multiplier",
            y="max_borrowings_to_be_liquidated",
        )
        st.plotly_chart(figure)
        end = time.time()
        print("updated in", end - start)

    if st.button("Update"):
        with st.spinner("Processing..."):
            update_state()
        st.success("Updated!")

    st.write(f"ETH price: ${prices.prices['ETH']}")


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="Carmine Dashboard",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
