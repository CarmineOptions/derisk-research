import logging
from collections import defaultdict
from functools import partial

import pandas as pd
import streamlit

import src.helpers
import src.main_chart
import src.settings

ZKLEND = "zkLend"
NOSTRA_ALPHA = "Nostra Alpha"
NOSTRA_MAINNET = "Nostra Mainnet"

PROTOCOL_NAMES = [
    ZKLEND,
    NOSTRA_ALPHA,
    NOSTRA_MAINNET,
]


class ProtocolColors:
    collateral_protocol_color_map = {
        ZKLEND: "#00ff00",
        NOSTRA_ALPHA: "#008000",
        NOSTRA_MAINNET: "#003300",
    }

    debt_protocol_color_map = {
        ZKLEND: "#ff3333",
        NOSTRA_ALPHA: "#ff0000",
        NOSTRA_MAINNET: "#660000",
    }

    supply_protocol_color_map = {
        ZKLEND: "#6666ff",
        NOSTRA_ALPHA: "#0000ff",
        NOSTRA_MAINNET: "#00004d",
    }


def parse_token_amounts(raw_token_amounts: str) -> dict[str, float]:
    """Converts token amounts in the string format to the dict format."""
    token_amounts = defaultdict(int)

    if raw_token_amounts == "":
        return token_amounts

    individual_token_parts = raw_token_amounts.split(", ")
    for individual_token_part in individual_token_parts:
        token, amount = individual_token_part.split(": ")
        token_amounts[token] += float(amount)

    return token_amounts


def create_stablecoin_bundle(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
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
                combined_df = pd.merge(
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


@streamlit.cache_data(ttl=300)
def get_data(
    protocol_name: str,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """
    Load loan data and main chart data for the specified protocol.
    :param protocol_name: Protocol name.
    :return: DataFrames containing loan data and main chart data.
    """
    return src.helpers.load_data(protocol=protocol_name)


def get_protocol_data_mappings(
    current_pair: str, stable_coin_pair: str, protocols: list[str]
) -> tuple[dict[str, dict], dict[str, dict]]:
    """
    Get protocol data mappings for main chart data and loans data.

    :param current_pair: The current pair for which data is to be fetched.
    :param stable_coin_pair: The stable coin pair to check against.
    :param protocols: List of protocols for which data is to be fetched.
    :return: tuple of dictionaries containing:
        - protocol_main_chart_data: Mapping of protocol names to their main chart data.
        - protocol_loans_data: Mapping of protocol names to their loans data.
    """

    protocol_main_chart_data: dict[str, dict] = {}
    protocol_loans_data: dict[str, dict] = {}

    for protocol_name in protocols:
        main_chart_data, loans_data = get_data(protocol_name)
        protocol_loans_data[protocol_name] = loans_data

        if current_pair == stable_coin_pair:
            protocol_main_chart_data[protocol_name] = create_stablecoin_bundle(
                main_chart_data
            )[current_pair]
        else:
            protocol_main_chart_data[protocol_name] = main_chart_data[current_pair]

    return protocol_main_chart_data, protocol_loans_data


def load_stats_data() -> (
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
):
    """
    Load general stats, supply stats, collateral stats, and debt stats data.
    :return: tuple of DataFrames containing general stats, supply stats, collateral stats, debt stats, and utilization stats.
    """
    BASE_GS_PATH = f"gs://{src.helpers.GS_BUCKET_NAME}/data"
    read_parquet_with_protocol_index = partial(pd.read_parquet, engine="fastparquet")

    @streamlit.cache_data(ttl=300)
    def read_and_set_index(file_path: str) -> pd.DataFrame:
        """
        Read a parquet file and set the index to 'Protocol'.
        :param file_path: file_path
        :return: DataFrame
        """
        return read_parquet_with_protocol_index(file_path).set_index("Protocol")

    # Read the parquet files
    general_stats = read_and_set_index(f"{BASE_GS_PATH}/general_stats.parquet")
    supply_stats = read_and_set_index(f"{BASE_GS_PATH}/supply_stats.parquet")
    collateral_stats = read_and_set_index(f"{BASE_GS_PATH}/collateral_stats.parquet")
    debt_stats = read_and_set_index(f"{BASE_GS_PATH}/debt_stats.parquet")

    # Calculate TVL (USD)
    general_stats["TVL (USD)"] = (
        supply_stats["Total supply (USD)"] - general_stats["Total debt (USD)"]
    )
    utilization_stats = read_and_set_index(f"{BASE_GS_PATH}/utilization_stats.parquet")

    return supply_stats, collateral_stats, debt_stats, general_stats, utilization_stats


def transform_loans_data(
    protocol_loans_data_mapping: pd.DataFrame, protocols: list[str]
) -> pd.DataFrame:
    """
    Transform protocol loans data
    :param protocol_loans_data_mapping: Input DataFrame.
    :param protocols: List of protocols.
    :return: Transformed loans DataFrame.
    """
    loans_data = pd.DataFrame()

    for protocol in protocols:
        protocol_loans_data = protocol_loans_data_mapping[protocol]
        if loans_data.empty:
            loans_data = protocol_loans_data
        else:
            loans_data = pd.concat([loans_data, protocol_loans_data])
    # Convert token amounts in the string format to the dict format.
    loans_data["Collateral"] = loans_data["Collateral"].apply(parse_token_amounts)
    loans_data["Debt"] = loans_data["Debt"].apply(parse_token_amounts)
    return loans_data


def transform_main_chart_data(
    protocol_main_chart_data_mapping: pd.DataFrame,
    current_pair: str,
    protocols: list[str],
) -> pd.DataFrame:
    """
    Transform the data for main_chart
    :param protocol_main_chart_data_mapping:
    :param current_pair: debt_token and collateral_token pair
    :param protocols: List of protocols
    :return: Transformed main chart DataFrame.
    """
    main_chart_data = pd.DataFrame()

    for protocol in protocols:
        protocol_main_chart_data = protocol_main_chart_data_mapping[protocol]
        if protocol_main_chart_data is None or protocol_main_chart_data.empty:
            logging.warning(f"No data for pair {current_pair} from {protocol}")
            collateral_token, debt_token = current_pair.split("-")
            streamlit.subheader(
                f":warning: No liquidable debt for the {collateral_token} collateral token and the {debt_token} debt token exists on the {protocol} protocol."
            )
            continue

        if main_chart_data.empty:
            main_chart_data = protocol_main_chart_data
            main_chart_data[f"liquidable_debt_{protocol}"] = protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data[f"liquidable_debt_at_interval_{protocol}"] = (
                protocol_main_chart_data["liquidable_debt_at_interval"]
            )
        else:
            main_chart_data["liquidable_debt"] += protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data["liquidable_debt_at_interval"] += protocol_main_chart_data[
                "liquidable_debt_at_interval"
            ]
            main_chart_data[f"liquidable_debt_{protocol}"] = protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data[f"liquidable_debt_at_interval_{protocol}"] = (
                protocol_main_chart_data["liquidable_debt_at_interval"]
            )

    return main_chart_data
