import decimal
import streamlit as st
import plotly.express

import classes
from data import load_graph_data, load_state
from histogram import visualization

# SESSION STATE
if "parameters" not in st.session_state:
    st.session_state["parameters"] = {
        "COLLATERAL_TOKEN": "ETH",
        "BORROWINGS_TOKEN": "USDC",
        "COLLATERAL_TOKEN_PRICE": decimal.Decimal("1500"),
        "X_AXIS_DESC": "collateral_token_price_multiplier",
        "Y_AXIS_DESC": "max_borrowings_to_be_liquidated",
    }

if "prices" not in st.session_state:
    st.session_state["prices"] = classes.Prices()


def main():
    st.title("DeRisk")
    load_state()
    visualization()


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
