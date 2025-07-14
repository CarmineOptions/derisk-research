import datetime
import difflib
import logging
import math

import numpy.random
import pandas
import plotly.express
import src.helpers
import src.main_chart
import src.persistent_state
import src.settings
import src.swap_amm
import src.utils
import streamlit
from src.chart_utils import (
    get_protocol_data_mappings,
    load_stats_data,
    transform_loans_data,
    transform_main_chart_data,
)
from src.helpers import (
    extract_token_addresses,
    fetch_token_symbols_from_set_of_loan_addresses,
    update_loan_data_with_symbols,
)

PROTOCOL_NAMES = [
    "zkLend",
    "Nostra Alpha",
    "Nostra Mainnet",
]  # "Hashstack V0", "Hashstack V1"


def infer_protocol_name(input_protocol: str, valid_protocols: list[str]) -> str:
    """Find the closest matching protocol name from a list of valid protocols using fuzzy matching.

    Args:
        input_protocol (str): The protocol name input by the user.
        valid_protocols (list[str]): A list of valid protocol names.

    Returns:
        str: The closest matching protocol name if found, otherwise returns the input protocol.
    """
    closest_match = difflib.get_close_matches(
        input_protocol, valid_protocols, n=1, cutoff=0.6
    )
    return closest_match and closest_match[0] or input_protocol


def _remove_leading_zeros(address: str) -> str:
    while address[2] == "0":
        address = f"0x{address[3:]}"
    return address


def create_stablecoin_bundle(
    data: dict[str, pandas.DataFrame],
) -> dict[str, pandas.DataFrame]:
    """
    Creates a stablecoin bundle by merging relevant DataFrames for collateral tokens and debt tokens.

    For each collateral token specified in `src.settings.COLLATERAL_TOKENS`, this function finds the
    relevant stablecoin pairs from the provided `data` dictionary and merges the corresponding DataFrames
    based on the 'collateral_token_price' column. It combines the debt and liquidity data for multiple
    stablecoin pairs and adds the result back to the `data` dictionary under a new key.

    Parameters:
    data (dict[str, pandas.DataFrame]): A dictionary where the keys are token pairs and the values are
                                        corresponding DataFrames containing price and supply data.

    Returns:
    dict[str, pandas.DataFrame]: The updated dictionary with the newly created stablecoin bundle added.
    """

    # Iterate over all collateral tokens defined in the settings
    for collateral in src.settings.COLLATERAL_TOKENS:
        # Find all relevant pairs that involve the current collateral and one of the debt tokens
        relevant_pairs = [
            pair
            for pair in data.keys()
            if collateral in pair
            and any(stablecoin in pair for stablecoin in src.settings.DEBT_TOKENS[:-1])
        ]
        combined_df = None  # Initialize a variable to store the combined DataFrame

        # Loop through each relevant pair
        for pair in relevant_pairs:
            df = data[pair]  # Get the DataFrame for the current pair

            if df.empty:
                # Log a warning if the DataFrame is empty and skip to the next pair
                logging.warning(f"Empty DataFrame for pair: {pair}")
                continue

            if combined_df is None:
                # If this is the first DataFrame being processed, use it as the base for combining
                combined_df = df.copy()
            else:
                # Merge the current DataFrame with the combined one on 'collateral_token_price'
                combined_df = pandas.merge(
                    combined_df, df, on="collateral_token_price", suffixes=("", "_y")
                )

                # Sum the columns for debt and liquidity, adding the corresponding '_y' values
                for col in [
                    "liquidable_debt",
                    "liquidable_debt_at_interval",
                    "10kSwap_debt_token_supply",
                    "MySwap_debt_token_supply",
                    "SithSwap_debt_token_supply",
                    "JediSwap_debt_token_supply",
                    "debt_token_supply",
                ]:
                    combined_df[col] += combined_df[f"{col}_y"]

                # Drop the '_y' columns after summing the relevant values
                combined_df.drop(
                    [col for col in combined_df.columns if col.endswith("_y")],
                    axis=1,
                    inplace=True,
                )

        # Create a new pair name for the stablecoin bundle
        new_pair = f"{collateral}-{src.settings.STABLECOIN_BUNDLE_NAME}"
        # Add the combined DataFrame for this collateral to the data dictionary
        data[new_pair] = combined_df

    # Return the updated data dictionary
    return data


def process_liquidity(
    main_chart_data: pandas.DataFrame, collateral_token: str, debt_token: str
) -> tuple[pandas.DataFrame, float]:
    """
    Process liquidity data for the main chart.
    :param main_chart_data: Main chart data.
    :param collateral_token: Collateral token.
    :param debt_token: Debt token.
    :return: Processed main chart data and collateral token price.
    """
    # Fetch underlying addresses and decimals
    collateral_token_underlying_address = (
        src.helpers.UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[collateral_token]
    )
    collateral_token_decimals = int(
        math.log10(src.settings.TOKEN_SETTINGS[collateral_token].decimal_factor)
    )
    underlying_addresses_to_decimals = {
        collateral_token_underlying_address: collateral_token_decimals
    }

    # Fetch prices
    prices = src.helpers.get_prices(token_decimals=underlying_addresses_to_decimals)
    collateral_token_price = prices[collateral_token_underlying_address]

    # Process main chart data
    main_chart_data = main_chart_data.astype(float)
    debt_token_underlying_address = (
        src.helpers.UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[debt_token]
    )

    ekubo_liquidity = src.utils.EkuboLiquidity(
        data=main_chart_data,
        collateral_token=collateral_token_underlying_address,
        debt_token=debt_token_underlying_address,
    )

    main_chart_data = ekubo_liquidity.apply_liquidity_to_dataframe(
        ekubo_liquidity.fetch_liquidity(),
    )

    return main_chart_data, collateral_token_price


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

    (
        protocol_main_chart_data_mapping,
        protocol_loans_data_mapping,
    ) = get_protocol_data_mappings(
        current_pair=current_pair,
        stable_coin_pair=stable_coin_pair,
        protocols=protocols,
    )
    loans_data = transform_loans_data(protocol_loans_data_mapping, protocols)
    # tobe
    loans_data_main = loans_data.copy()
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

    if not loans_data.empty:
        token_addresses = extract_token_addresses(loans_data)
        if token_addresses:
            # tobe
            token_symbols = fetch_token_symbols_from_set_of_loan_addresses(
                token_addresses
            )
            loans_data = update_loan_data_with_symbols(loans_data, token_symbols)
        # tobe
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
                loans_data[
                    loans_data["Health factor"] > 1  # TODO: debug the negative HFs
                ]
                .sort_values("Collateral (USD)", ascending=False)
                .iloc[:20],
                use_container_width=True,
            )
        with col2:
            streamlit.subheader("Sorted by debt")
            streamlit.dataframe(
                loans_data[
                    loans_data["Health factor"] > 1  # TODO: debug the negative HFs
                ]
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

            # Normalize the user address by adding leading zeroes if necessary
            user = src.helpers.add_leading_zeros(user)

            # Infer the correct protocol name using fuzzy matching
            valid_protocols = loans_data["Protocol"].unique()
            protocol = infer_protocol_name(protocol, valid_protocols)

        loan = loans_data_main.loc[
            (loans_data["User"] == user) & (loans_data["Protocol"] == protocol),
        ]

        if loan.empty:
            streamlit.warning(
                f"No loan found for user = {user} and protocol = {protocol}."
            )
        else:
            (
                collateral_usd_amounts,
                debt_usd_amounts,
            ) = src.main_chart.get_specific_loan_usd_amounts(loan=loan)

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

            streamlit.dataframe(update_loan_data_with_symbols(loan, token_symbols))

    streamlit.header("Comparison of lending protocols")
    (
        supply_stats,
        collateral_stats,
        debt_stats,
        general_stats,
        utilization_stats,
    ) = load_stats_data()
    # Display dataframes
    streamlit.dataframe(general_stats)
    streamlit.dataframe(utilization_stats)
    # USD deposit, collateral and debt per token (bar chart).
    (
        supply_figure,
        collateral_figure,
        debt_figure,
    ) = src.main_chart.get_bar_chart_figures(
        supply_stats=supply_stats.copy(),
        collateral_stats=collateral_stats.copy(),
        debt_stats=debt_stats.copy(),
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
