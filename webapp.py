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

X_AXIS_DESC = "collateral_token_price_multiplier"
Y_AXIS_DESC = "max_borrowings_to_be_liquidated"

prices = classes.Prices()

# SESSION STATE
if "latest_block" not in st.session_state:
    st.session_state["latest_block"] = 0
if "state" not in st.session_state:
    st.session_state["state"] = classes.State()
if "data" not in st.session_state:
    st.session_state["data"] = pandas.DataFrame(
        {
            X_AXIS_DESC: [
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
    st.title("DeRisk")

    def update_state():
        start = time.time()
        # get new events
        events = get_events()
        for _, event in events.iterrows():
            st.session_state.state.process_event(event=event)
        # update prices
        st.session_state.data[X_AXIS_DESC] = st.session_state.data[X_AXIS_DESC].map(
            decimal.Decimal
        )
        st.session_state.data[Y_AXIS_DESC] = st.session_state.data[X_AXIS_DESC].apply(
            lambda x: simulate_liquidations_under_price_change(
                prices=prices,
                collateral_token=COLLATERAL_TOKEN,
                collateral_token_price_multiplier=x,
                state=st.session_state.state,
                borrowings_token=BORROWINGS_TOKEN,
            )
        )
        end = time.time()
        print("updated in", end - start)

    if st.button("Update"):
        with st.spinner("Processing..."):
            update_state()
        st.success("Updated!")

    if Y_AXIS_DESC in st.session_state.data:
        figure = plotly.express.bar(
            st.session_state.data,
            x=X_AXIS_DESC,
            y=Y_AXIS_DESC,
        )
        st.plotly_chart(figure)

    st.write(f"ETH price: ${prices.prices['ETH']}")


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
