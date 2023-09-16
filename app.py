import datetime
import json
import multiprocessing
import os

import pandas
import plotly.express
import streamlit

import src.hashstack
import src.histogram
import update_data


# TODO: Introduce other pairs.
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


def load_data():
    data = {}
    for pair in PAIRS:
        data[pair] = pandas.read_csv(f"data/{pair}.csv")
    small_loans_sample = pandas.read_csv("data/small_loans_sample.csv")
    large_loans_sample = pandas.read_csv("data/large_loans_sample.csv")
    with open("data/last_update.json", "r") as f:
        last_update = json.load(f)
    last_updated = last_update["timestamp"]
    last_block_number = last_update["block_number"]
    return (
        data,
        small_loans_sample,
        large_loans_sample,
        last_updated,
        last_block_number,
    )


def main():
    streamlit.title("DeRisk")

    (
        data,
        small_loans_sample,
        large_loans_sample,
        last_updated,
        last_block_number,
    ) = load_data()
    (
        hashstack_data,
        hashstack_histogram_data,
        hashstack_small_loans_sample,
        hashstack_large_loans_sample,
    ) = src.hashstack.load_data()
    (
        nostra_data,
        nostra_histogram_data,
        nostra_small_loans_sample,
        nostra_large_loans_sample,
    ) = src.nostra.load_data()

    col1, _ = streamlit.columns([1, 4])

    with col1:
        protocols = streamlit.multiselect(
            label="Select protocols",
            options=["zkLend", "Hashstack", "Nostra"],
            default=["zkLend", "Hashstack", "Nostra"],
        )
        current_pair = streamlit.selectbox(
            label="Select collateral-loan pair:",
            options=PAIRS,
            index=0,
        )

    # TODO: refactor this mess
    if protocols == ["zkLend"]:
        data[current_pair] = data[current_pair]
        small_loans_sample = small_loans_sample
        large_loans_sample = large_loans_sample
    elif protocols == ["Hashstack"]:
        data[current_pair] = hashstack_data[current_pair]
        small_loans_sample = hashstack_small_loans_sample
        large_loans_sample = hashstack_large_loans_sample
    elif protocols == ["Nostra"]:
        data[current_pair] = nostra_data[current_pair]
        small_loans_sample = nostra_small_loans_sample
        large_loans_sample = nostra_large_loans_sample
    elif set(protocols) == {"zkLend", "Hashstack"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] += hashstack_data[
            current_pair
        ]["max_borrowings_to_be_liquidated"]
        data[current_pair][
            "max_borrowings_to_be_liquidated_at_interval"
        ] += hashstack_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        small_loans_sample = (
            pandas.concat([small_loans_sample, hashstack_small_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
        large_loans_sample = (
            pandas.concat([large_loans_sample, hashstack_large_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
    elif set(protocols) == {"zkLend", "Nostra"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] += nostra_data[
            current_pair
        ]["max_borrowings_to_be_liquidated"]
        data[current_pair][
            "max_borrowings_to_be_liquidated_at_interval"
        ] += nostra_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        small_loans_sample = (
            pandas.concat([small_loans_sample, nostra_small_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
        large_loans_sample = (
            pandas.concat([large_loans_sample, nostra_large_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
    elif set(protocols) == {"Hashstack", "Nostra"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] = (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated"]
        )
        data[current_pair]["max_borrowings_to_be_liquidated_at_interval"] = (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        )
        small_loans_sample = (
            pandas.concat([hashstack_small_loans_sample, nostra_small_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
        large_loans_sample = (
            pandas.concat([hashstack_large_loans_sample, nostra_large_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
    elif set(protocols) == {"zkLend", "Hashstack", "Nostra"}:
        data[current_pair]["max_borrowings_to_be_liquidated"] += (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated"]
        )
        data[current_pair]["max_borrowings_to_be_liquidated_at_interval"] += (
            hashstack_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
            + nostra_data[current_pair]["max_borrowings_to_be_liquidated_at_interval"]
        )
        small_loans_sample = (
            pandas.concat([small_loans_sample, hashstack_small_loans_sample, nostra_small_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )
        large_loans_sample = (
            pandas.concat([large_loans_sample, hashstack_large_loans_sample, nostra_large_loans_sample])
            .sort_values("Health factor")
            .iloc[:20]
        )

    [col, bor] = current_pair.split("-")

    color_map = {
        "max_borrowings_to_be_liquidated_at_interval": "#ECD662",
        "amm_borrowings_token_supply": "#4CA7D0",
    }

    figure = plotly.express.bar(
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

    streamlit.plotly_chart(figure, True)

    streamlit.header("Loans with low health factor")
    streamlit.table(small_loans_sample)
    streamlit.header("Sizeable loans with low health factor")
    streamlit.table(large_loans_sample)

    streamlit.header("Comparison of lending protocols")
    comparison_stats = pandas.read_csv("comparison_stats.csv")
    streamlit.table(comparison_stats)

    streamlit.header("Loan size distribution")
    src.histogram.visualization(protocols)

    date_str = datetime.datetime.utcfromtimestamp(int(last_updated))
    streamlit.write(f"Last updated {date_str} UTC, last block: {last_block_number}")


if __name__ == "__main__":
    streamlit.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    if os.environ.get("UPDATE_RUNNING") is None:
        os.environ["UPDATE_RUNNING"] = "True"
        # TODO: Switch to logging.
        print("Spawning the updating process.", flush=True)
        update_data_process = multiprocessing.Process(
            target=update_data.update_data_continuously, daemon=True
        )
        update_data_process.start()
    main()
