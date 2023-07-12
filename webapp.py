import decimal
import pandas
import streamlit as st
import plotly.express

import classes
from compute import compute_max_liquidated_amount, decimal_range
from get_data import get_events

import copy


COLLATERAL_TOKEN = "wBTC"
BORROWINGS_TOKEN = "USDC"
COLLATERAL_TOKEN_PRICE_MULTIPLIER = decimal.Decimal("0.99")
COLLATERAL_TOKEN = "ETH"
BORROWINGS_TOKEN = "USDC"
state = classes.State()
prices = classes.Prices()
data = pandas.DataFrame(
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


simulate_liquidations_under_price_change(
    prices=prices,
    collateral_token=COLLATERAL_TOKEN,
    collateral_token_price_multiplier=COLLATERAL_TOKEN_PRICE_MULTIPLIER,
    state=state,
    borrowings_token=BORROWINGS_TOKEN,
)


def main():
    st.title("DeRisk by Carmine Finance")

    def update_state():
        # get new events
        events = get_events()
        for _, event in events.iterrows():
            state.process_event(event=event)
        # update prices
        prices.get_prices()
        data["collateral_token_price_multiplier"] = data[
            "collateral_token_price_multiplier"
        ].map(decimal.Decimal)
        data["max_borrowings_to_be_liquidated"] = data[
            "collateral_token_price_multiplier"
        ].apply(
            lambda x: simulate_liquidations_under_price_change(
                prices=prices,
                collateral_token=COLLATERAL_TOKEN,
                collateral_token_price_multiplier=x,
                state=state,
                borrowings_token=BORROWINGS_TOKEN,
            )
        )
        data

    if st.button("Update"):
        with st.spinner("Processing..."):
            update_state()
        st.success("Updated!")

    st.write(f"ETH price: ${prices.prices['ETH']}")
    figure = plotly.express.bar(
        data, x="collateral_token_price_multiplier", y="max_borrowings_to_be_liquidated"
    )
    st.plotly_chart(figure)


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="Carmine Dashboard",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
