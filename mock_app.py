import streamlit as st
import plotly.express as px
import pandas as pd

from histogram import visualization

PAIRS = [
    "ETH-USDC",
    "ETH-USDT",
    "ETH-DAI",
    "wBTC-USDC",
    "wBTC-USDT",
    "wBTC-DAI",
    # "ETH-wBTC",
    # "wBTC-ETH",
]


@st.cache_data()
def load_data():
    data = {}
    for pair in PAIRS:
        data[pair] = pd.read_csv(f"{pair}.csv")

    histogram_data = pd.read_csv("histogram.csv")
    return (data, histogram_data)


def main():
    st.title("DeRisk")

    (data, histogram_data) = load_data()

    col1, _ = st.columns([1, 4])

    with col1:
        current_pair = st.selectbox(
            label="Select collateral-loan pair:",
            options=PAIRS,
            index=0,
        )

    [col, bor] = current_pair.split("-")

    color_map = {
        "max_borrowings_to_be_liquidated_at_interval": "#ECD662",
        "amm_borrowings_token_supply": "#4CA7D0",
    }

    figure = px.bar(
        data[current_pair].astype(float),
        x="collateral_token_price",
        y=[
            "max_borrowings_to_be_liquidated_at_interval",
            "amm_borrowings_token_supply",
        ],
        title=f"Potentially liquidatable amounts of {bor} loans and the corresponding supply of {col}",
        barmode="overlay",
        opacity=0.65,
        color_discrete_map=color_map,
    )
    figure.update_traces(hovertemplate=("<b>Price:</b> %{x}<br>" "<b>Volume:</b> %{y}"))
    figure.update_traces(
        selector=dict(name="max_borrowings_to_be_liquidated_at_interval"),
        name="Liquidable",
    )
    figure.update_traces(
        selector=dict(name="amm_borrowings_token_supply"), name="AMM Supply"
    )
    figure.update_xaxes(title_text=f"{col} price")
    figure.update_yaxes(title_text="Volume")

    st.plotly_chart(figure, True)

    small_loans_sample = pd.read_csv("small_loans_sample.csv")
    large_loans_sample = pd.read_csv("large_loans_sample.csv")
    st.header("Loans with low health factor")
    st.table(small_loans_sample)
    st.header("Sizeable loans with low health factor")
    st.table(large_loans_sample)
    st.header("Loan size distribution")
    visualization(histogram_data)


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
