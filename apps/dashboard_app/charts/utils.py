"""
This moudel process and transform liquidity, loan, and chart data for protocols.
"""

import asyncio
import logging
import math
import time
from collections import defaultdict

import pandas as pd
import streamlit as st
from data_handler.handlers.loan_states.abstractions import State
from shared.amms import SwapAmm
from shared.constants import PAIRS

from helpers.ekubo import EkuboLiquidity
from helpers.loans_table import get_loans_table_data
from helpers.settings import (
    COLLATERAL_TOKENS,
    DEBT_TOKENS,
    STABLECOIN_BUNDLE_NAME,
    TOKEN_SETTINGS,
    UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES,
)
from helpers.tools import get_main_chart_data, get_prices

logger = logging.getLogger(__name__)


def process_liquidity(
    main_chart_data: pd.DataFrame, collateral_token: str, debt_token: str
) -> tuple[pd.DataFrame, float]:
    """
    Process liquidity data for the main chart.
    :param main_chart_data: Main chart data.
    :param collateral_token: Collateral token.
    :param debt_token: Debt token.
    :return: Processed main chart data and collateral token price.
    """
    # Fetch underlying addresses and decimals
    collateral_token_underlying_address = UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[
        collateral_token
    ]
    collateral_token_decimals = int(
        math.log10(TOKEN_SETTINGS[collateral_token].decimal_factor)
    )
    underlying_addresses_to_decimals = {
        collateral_token_underlying_address: collateral_token_decimals
    }

    # Fetch prices
    prices = get_prices(token_decimals=underlying_addresses_to_decimals)
    collateral_token_price = prices[collateral_token_underlying_address]

    # Process main chart data
    main_chart_data = main_chart_data.astype(float)
    debt_token_underlying_address = UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[
        debt_token
    ]

    ekubo_liquidity = EkuboLiquidity(
        data=main_chart_data,
        collateral_token=collateral_token_underlying_address,
        debt_token=debt_token_underlying_address,
    )

    main_chart_data = ekubo_liquidity.apply_liquidity_to_dataframe(
        ekubo_liquidity.fetch_liquidity(),
    )

    return main_chart_data, collateral_token_price


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
    Creates a stablecoin bundle by merging relevant DataFrames for collateral tokens and debt
    tokens.

    For each collateral token specified in `src.settings.COLLATERAL_TOKENS`, this function finds
    the relevant stablecoin pairs from the provided `data` dictionary and merges the corresponding
    Dataframes based on the 'collateral_token_price' column. It combines the debt and liquidity
    data for multiple stablecoin pairs and adds the result back to the `data` dictionary under a
    new key.

    Parameters:
    data (dict[str, pandas.DataFrame]): A dictionary where the keys are token pairs and the values
     are corresponding DataFrames containing price and supply data.

    Returns: dict[str, pandas.DataFrame]:
    The updated dictionary with the newly created stablecoin bundle added.
    """

    # Iterate over all collateral tokens defined in the settings
    for collateral in COLLATERAL_TOKENS:
        # Find all relevant pairs that involve the current collateral and one of the debt tokens
        relevant_pairs = [
            pair
            for pair in data.keys()
            if collateral in pair
            and any(stablecoin in pair for stablecoin in DEBT_TOKENS[:-1])
        ]
        combined_df = None  # Initialize a variable to store the combined DataFrame

        # Loop through each relevant pair
        for pair in relevant_pairs:
            df = data[pair]  # Get the DataFrame for the current pair

            if df.empty:
                # Log a warning if the DataFrame is empty and skip to the next pair
                logging.warning("Empty DataFrame for pair: %s", pair)
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
        new_pair = f"{collateral}-{STABLECOIN_BUNDLE_NAME}"
        # Add the combined DataFrame for this collateral to the data dictionary
        data[new_pair] = combined_df

    # Return the updated data dictionary
    return data


def get_data(
    protocol_name: str, state: State
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Load loan data and main chart data for the specified protocol.
    :param protocol_name: Protocol name.
    :param state: State to load data for.
    :return: DataFrames containing loan data and main chart data.
    """
    main_chart_data = {}
    underlying_addresses_to_decimals = {
        x.address: int(math.log10(x.decimal_factor)) for x in TOKEN_SETTINGS.values()
    }
    current_prices = get_prices(token_decimals=underlying_addresses_to_decimals)
    t_swap = time.time()
    swap_amm = SwapAmm()
    swap_amm.__init__()
    asyncio.run(swap_amm.get_balance())
    logging.info(f"swap in {time.time() - t_swap}s")

    for pair in PAIRS:
        collateral_token_underlying_symbol, debt_token_underlying_symbol = pair.split(
            "-"
        )
        try:
            main_chart_data[pair] = get_main_chart_data(
                state=state,
                prices=current_prices,
                swap_amms=swap_amm,
                collateral_token_underlying_symbol=collateral_token_underlying_symbol,
                debt_token_underlying_symbol=debt_token_underlying_symbol,
            )
        except Exception:
            main_chart_data[pair] = pd.DataFrame()

    loans_data = get_loans_table_data(state=state, prices=current_prices)
    return main_chart_data, loans_data


def get_protocol_data_mappings(
    current_pair: str, stable_coin_pair: str, protocols: list[str], state: State
) -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
    """
    Get protocol data mappings for main chart data and loans data.

    :param current_pair: The current pair for which data is to be fetched.
    :param stable_coin_pair: The stable coin pair to check against.
    :param protocols: List of protocols for which data is to be fetched.
    :param state: State to load data for.
    :return: tuple of dictionaries containing:
        - protocol_main_chart_data: Mapping of protocol names to their main chart data.
        - protocol_loans_data: Mapping of protocol names to their loans data.
    """

    protocol_main_chart_data: dict[str, pd.DataFrame] = {}
    protocol_loans_data: dict[str, dict] = {}

    for protocol_name in protocols:
        main_chart_data, loans_data = get_data(state=state, protocol_name=protocol_name)
        protocol_loans_data[protocol_name] = loans_data

        if current_pair == stable_coin_pair:
            protocol_main_chart_data[protocol_name] = create_stablecoin_bundle(
                main_chart_data
            )[current_pair]
        else:
            protocol_main_chart_data[protocol_name] = main_chart_data[current_pair]

    return protocol_main_chart_data, protocol_loans_data


def transform_loans_data(
    protocol_loans_data_mapping: dict[str, dict], protocols: list[str]
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
            logging.warning("No data for pair %s from %s", current_pair, protocol)
            collateral_token, debt_token = current_pair.split("-")
            st.subheader(
                f":warning: No liquidable debt for the {collateral_token} collateral token and "
                f"the {debt_token} debt token exists on the {protocol} protocol."
            )
            continue

        if main_chart_data.empty:
            main_chart_data = protocol_main_chart_data
            main_chart_data[f"liquidable_debt_{protocol}"] = protocol_main_chart_data[
                "liquidable_debt"
            ]
            main_chart_data[
                f"liquidable_debt_at_interval_{protocol}"
            ] = protocol_main_chart_data["liquidable_debt_at_interval"]
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
            main_chart_data[
                f"liquidable_debt_at_interval_{protocol}"
            ] = protocol_main_chart_data["liquidable_debt_at_interval"]

    return main_chart_data
