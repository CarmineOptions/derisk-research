from datetime import datetime
import json
import multiprocessing
import os
import streamlit as st
import plotly.express as px
import pandas as pd

from src.histogram import visualization
from update_data import update_data_continuously
import src.hashstack

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


@st.cache_data(ttl=120)
def load_data():
    data = {}
    for pair in PAIRS:
        data[pair] = pd.read_csv(f"data/{pair}.csv")
    histogram_data = pd.read_csv("data/histogram.csv")
    small_loans_sample = pd.read_csv("data/small_loans_sample.csv")
    large_loans_sample = pd.read_csv("data/large_loans_sample.csv")
    with open("data/last_update.json", "r") as f:
        last_update = json.load(f)
    last_updated = last_update["timestamp"]
    last_block_number = last_update["block_number"]
    return (
        data,
        histogram_data,
        small_loans_sample,
        large_loans_sample,
        last_updated,
        last_block_number,
    )


def main():
    st.title("DeRisk")

    (
        data,
        histogram_data,
        small_loans_sample,
        large_loans_sample,
        last_updated,
        last_block_number,
    ) = load_data()
    (
        hashstack_data,
#         hashstack_histogram_data,
        hashstack_small_loans_sample,
        hashstack_large_loans_sample,
    ) = src.hashstack.load_data()

    col1, _ = st.columns([1, 4])

    protocols = st.multiselect(
        label = 'Select protocols',
        options = ['zkLend', 'Hashstack'],
    )

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
    figure.update_traces(hovertemplate=(
        "<b>Price:</b> %{x}<br>" "<b>Volume:</b> %{y}"))
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

    st.header("Loans with low health factor")
    st.table(small_loans_sample)
    st.header("Sizeable loans with low health factor")
    st.table(large_loans_sample)
    st.header("Loan size distribution")
    visualization(histogram_data)

    date_str = datetime.utcfromtimestamp(int(last_updated))
    st.write(f"Last updated {date_str} UTC, last block: {last_block_number}")


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    if os.environ.get("UPDATE_RUNNING") is None:
        os.environ["UPDATE_RUNNING"] = "True"
        print("Spawning updating process", flush=True)
        update_data_process = multiprocessing.Process(
            target=update_data_continuously)
        update_data_process.start()
    main()
