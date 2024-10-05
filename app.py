import datetime
import logging
import time

import numpy
import pandas
import plotly
import requests
import streamlit

import src.helpers
import src.main_chart
import src.persistent_state
import src.settings
import src.swap_amm
from chart_utils import (get_protocol_data_mappings, load_stats_data,
                         transform_loans_data, transform_main_chart_data)

PROTOCOL_NAMES = [
    "zkLend",
    "Nostra Alpha",
    "Nostra Mainnet",
]  # "Hashstack V0", "Hashstack V1"


def _remove_leading_zeros(address: str) -> str:
    while address[2] == "0":
        address = f"0x{address[3:]}"
    return address


def _get_available_liquidity(
    data: pandas.DataFrame, price: float, price_diff: float, bids: bool
) -> float:
    price_lower_bound = max(0.95 * price, price - price_diff) if bids else price
    price_upper_bound = price if bids else min(1.05 * price, price + price_diff)
    return data.loc[
        data["price"].between(price_lower_bound, price_upper_bound), "quantity"
    ].sum()


def add_ekubo_liquidity(
    data: pandas.DataFrame,
    collateral_token: str,
    debt_token: str,
) -> float:
    URL = "http://178.32.172.153/orderbook/"
    DEX = "Ekubo"
    params = {
        "base_token": _remove_leading_zeros(collateral_token),
        "quote_token": _remove_leading_zeros(debt_token),
        "dex": DEX,
    }
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        liquidity = response.json()
        try:
            bid_prices, bid_quantities = zip(*liquidity["bids"])
        except ValueError:
            time.sleep(300)
            add_ekubo_liquidity(
                data=data, collateral_token=collateral_token, debt_token=debt_token
            )
        else:
            bids = pandas.DataFrame(
                {
                    "price": bid_prices,
                    "quantity": bid_quantities,
                },
            )
            bids = bids.astype(float)
            bids.sort_values("price", inplace=True)
            price_diff = data["collateral_token_price"].diff().max()
            data["Ekubo_debt_token_supply"] = data["collateral_token_price"].apply(
                lambda x: _get_available_liquidity(
                    data=bids,
                    price=x,
                    price_diff=price_diff,
                    bids=True,
                )
            )
            data["debt_token_supply"] += data["Ekubo_debt_token_supply"]
            return data

    logging.warning(
        "Using collateral token as base token and debt token as quote token."
    )
    params = {
        "base_token": _remove_leading_zeros(debt_token),
        "quote_token": _remove_leading_zeros(collateral_token),
        "dex": DEX,
    }
    response = requests.get(URL, params=params)

    if response.status_code == 200:
        liquidity = response.json()
        try:
            ask_prices, ask_quantities = zip(*liquidity["asks"])
        except ValueError:
            time.sleep(5)
            add_ekubo_liquidity(
                data=data, collateral_token=collateral_token, debt_token=debt_token
            )
        else:
            asks = pandas.DataFrame(
                {
                    "price": ask_prices,
                    "quantity": ask_quantities,
                },
            )
            asks = asks.astype(float)
            asks.sort_values("price", inplace=True)
            data["Ekubo_debt_token_supply"] = data["collateral_token_price"].apply(
                lambda x: _get_available_liquidity(
                    data=asks,
                    price=x,
                    bids=False,
                )
            )
            data["debt_token_supply"] += data["Ekubo_debt_token_supply"]
            return data

    return data


def main():
    streamlit.title("DeRisk")

    col1, _ = streamlit.columns([1, 3])
    with col1:
        protocols = streamlit.multiselect(
            label="Select protocols",
            options=PROTOCOL_NAMES,
            default=PROTOCOL_NAMES,
        )
        collateral_token = streamlit.selectbox(
            label="Select collateral token:",
            options=src.settings.COLLATERAL_TOKENS,
            index=0,
        )

        debt_token = streamlit.selectbox(
            label="Select debt token:",
            options=src.settings.DEBT_TOKENS,
            index=0,
        )
    stable_coin_pair = f"{collateral_token}-{src.settings.STABLECOIN_BUNDLE_NAME}"

    if debt_token == collateral_token:
        streamlit.subheader(
            f":warning: You are selecting the same token for both collateral and debt."
        )

    current_pair = f"{collateral_token}-{debt_token}"

    protocol_main_chart_data_mapping, protocol_loans_data_mapping = (
        get_protocol_data_mappings(
            current_pair=current_pair,
            stable_coin_pair=stable_coin_pair,
            protocols=protocols,
        )
    )
    loans_data = transform_loans_data(protocol_loans_data_mapping, protocols)
    main_chart_data = transform_main_chart_data(
        protocol_main_chart_data_mapping, current_pair, protocols
    )

    # Plot the liquidable debt against the available supply.
    collateral_token, debt_token = current_pair.split("-")
    collateral_token_price = 0

    if current_pair == stable_coin_pair:
        for stable_coin in src.settings.DEBT_TOKENS[:-1]:
            debt_token = stable_coin
            main_chart_data, collateral_token_price = process_liquidity(
                main_chart_data, collateral_token, debt_token
            )
    else:
        main_chart_data, collateral_token_price = process_liquidity(
            main_chart_data, collateral_token, debt_token
        )

    # TODO: Add Ekubo end
    figure = src.main_chart.get_main_chart_figure(
        data=main_chart_data,
        collateral_token=collateral_token,
        debt_token=(
            src.settings.STABLECOIN_BUNDLE_NAME
            if current_pair == stable_coin_pair
            else debt_token
        ),
        collateral_token_price=collateral_token_price,
    )
    streamlit.plotly_chart(figure_or_data=figure, use_container_width=True)

    main_chart_data["debt_to_supply_ratio"] = (
        main_chart_data["liquidable_debt_at_interval"]
        / main_chart_data["debt_token_supply"]
    )
    example_rows = main_chart_data[
        (main_chart_data["debt_to_supply_ratio"] > 0.75)
        & (main_chart_data["collateral_token_price"] <= collateral_token_price)
    ]

    if not example_rows.empty:
        example_row = example_rows.sort_values("collateral_token_price").iloc[-1]

        def _get_risk_level(debt_to_supply_ratio: float) -> str:
            if debt_to_supply_ratio < 0.2:
                return "low"
            elif debt_to_supply_ratio < 0.4:
                return "medium"
            elif debt_to_supply_ratio < 0.6:
                "high"
            return "very high"

        streamlit.subheader(
            f":warning: At price of {round(example_row['collateral_token_price'], 2)}, the risk of acquiring bad debt for "
            f"lending protocols is {_get_risk_level(example_row['debt_to_supply_ratio'])}."
        )
        streamlit.write(
            f"The ratio of liquidated debt to available supply is {round(example_row['debt_to_supply_ratio'] * 100)}%.Debt"
            f" worth of {int(example_row['liquidable_debt_at_interval']):,} USD will be liquidated while the AMM swaps "
            f"capacity will be {int(example_row['debt_token_supply']):,} USD."
        )

    streamlit.header("Liquidable debt")
    liquidable_debt_data = main_chart_data[
        ["collateral_token_price", "liquidable_debt_at_interval", "liquidable_debt"]
    ].copy()
    liquidable_debt_data.rename(
        columns={
            "liquidable_debt": "Liquidable debt at price",
            "liquidable_debt_at_interval": "Liquidable debt at interval",
            "collateral_token_price": "Collateral token price",
        },
        inplace=True,
    )

    # Display the filtered DataFrame and hide the index
    streamlit.dataframe(
        liquidable_debt_data.round(), use_container_width=True, hide_index=True
    )

    streamlit.header("Loans with low health factor")
    col1, _ = streamlit.columns([1, 3])
    with col1:
        debt_usd_lower_bound, debt_usd_upper_bound = streamlit.slider(
            label="Select range of USD borrowings",
            min_value=0,
            max_value=int(loans_data["Debt (USD)"].max()),
            value=(0, int(loans_data["Debt (USD)"].max())),
        )
    streamlit.dataframe(
        loans_data[
            (loans_data["Health factor"] > 0)  # TODO: debug the negative HFs
            & loans_data["Debt (USD)"].between(
                debt_usd_lower_bound, debt_usd_upper_bound
            )
        ]
        .sort_values("Health factor")
        .iloc[:20],
        use_container_width=True,
    )

    streamlit.header("Top loans")
    col1, col2 = streamlit.columns(2)
    with col1:
        streamlit.subheader("Sorted by collateral")
        streamlit.dataframe(
            loans_data[loans_data["Health factor"] > 1]  # TODO: debug the negative HFs
            .sort_values("Collateral (USD)", ascending=False)
            .iloc[:20],
            use_container_width=True,
        )
    with col2:
        streamlit.subheader("Sorted by debt")
        streamlit.dataframe(
            loans_data[loans_data["Health factor"] > 1]  # TODO: debug the negative HFs
            .sort_values("Debt (USD)", ascending=False)
            .iloc[:20],
            use_container_width=True,
        )

    streamlit.header("Detail of a loan")
    col1, col2, col3 = streamlit.columns(3)
    with col1:
        user = streamlit.text_input("User")
        protocol = streamlit.text_input("Protocol")

        users_and_protocols_with_debt = list(
            loans_data.loc[
                loans_data["Debt (USD)"] > 0,
                ["User", "Protocol"],
            ].itertuples(index=False, name=None)
        )

        random_user, random_protocol = users_and_protocols_with_debt[
            numpy.random.randint(len(users_and_protocols_with_debt))
        ]

        if not user:
            streamlit.write(f"Selected random user = {random_user}.")
            user = random_user
        if not protocol:
            streamlit.write(f"Selected random protocol = {random_protocol}.")
            protocol = random_protocol

    loan = loans_data.loc[
        (loans_data["User"] == user) & (loans_data["Protocol"] == protocol),
    ]

    if loan.empty:
        streamlit.warning(f"No loan found for user = {user} and protocol = {protocol}.")
    else:
        collateral_usd_amounts, debt_usd_amounts = (
            src.main_chart.get_specific_loan_usd_amounts(loan=loan)
        )

        with col2:
            figure = plotly.express.pie(
                collateral_usd_amounts,
                values="amount_usd",
                names="token",
                title="Collateral (USD)",
                color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
            )
            streamlit.plotly_chart(figure, True)

        with col3:
            figure = plotly.express.pie(
                debt_usd_amounts,
                values="amount_usd",
                names="token",
                title="Debt (USD)",
                color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
            )
            streamlit.plotly_chart(figure, True)

        streamlit.dataframe(loan)

    streamlit.header("Comparison of lending protocols")
    supply_stats, collateral_stats, debt_stats, general_stats, utilization_stats = (
        load_stats_data()
    )
    # Display dataframes
    streamlit.dataframe(general_stats)
    streamlit.dataframe(utilization_stats)
    # USD deposit, collateral and debt per token (bar chart).
    supply_figure, collateral_figure, debt_figure = (
        src.main_chart.get_bar_chart_figures(
            supply_stats=supply_stats.copy(),
            collateral_stats=collateral_stats.copy(),
            debt_stats=debt_stats.copy(),
        )
    )
    streamlit.plotly_chart(figure_or_data=supply_figure, use_container_width=True)
    streamlit.plotly_chart(figure_or_data=collateral_figure, use_container_width=True)
    streamlit.plotly_chart(figure_or_data=debt_figure, use_container_width=True)

    columns = streamlit.columns(4)
    tokens = list(src.settings.TOKEN_SETTINGS.keys())
    for column, token_1, token_2 in zip(columns, tokens[:4], tokens[4:]):
        with column:
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    collateral_stats.reset_index(),
                    values=f"{token} collateral",
                    names="Protocol",
                    title=f"{token} collateral",
                    color_discrete_sequence=plotly.express.colors.sequential.Oranges_r,
                )
                streamlit.plotly_chart(figure, True)
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    debt_stats.reset_index(),
                    values=f"{token} debt",
                    names="Protocol",
                    title=f"{token} debt",
                    color_discrete_sequence=plotly.express.colors.sequential.Greens_r,
                )
                streamlit.plotly_chart(figure, True)
            for token in [token_1, token_2]:
                figure = plotly.express.pie(
                    supply_stats.reset_index(),
                    values=f"{token} supply",
                    names="Protocol",
                    title=f"{token} supply",
                    color_discrete_sequence=plotly.express.colors.sequential.Blues_r,
                )
                streamlit.plotly_chart(figure, True)

    last_update = src.persistent_state.load_pickle(
        path=src.persistent_state.LAST_UPDATE_FILENAME
    )
    last_timestamp = last_update["timestamp"]
    last_block_number = last_update["block_number"]
    date_str = datetime.datetime.utcfromtimestamp(int(last_timestamp))
    streamlit.write(f"Last updated {date_str} UTC, last block: {last_block_number}.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    streamlit.set_page_config(
        layout="wide",
        page_title="DeRisk by Carmine Finance",
        page_icon="https://carmine.finance/assets/logo.svg",
    )

    main()
