"""
This moudel process and transform liquidity, loan, and chart data for protocols.
"""

import os
import asyncio
from decimal import Decimal
import difflib
import json
import logging
import math
import time
from collections import defaultdict

import pandas as pd
from shared.redis_client import redis_client
import streamlit as st
from shared.state import State
from shared.amms import SwapAmm, SwapAmmToken
from shared.constants import PAIRS

from dashboard_app.helpers.ekubo import EkuboLiquidity
from dashboard_app.helpers.loans_table import get_loans_table_data
from dashboard_app.helpers.settings import (
    COLLATERAL_TOKENS,
    DEBT_TOKENS,
    STABLECOIN_BUNDLE_NAME,
    TOKEN_SETTINGS,
    UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES,
)
from dashboard_app.helpers.tools import get_main_chart_data, get_prices

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


def streamlit_dev_fill_with_test_data():
    """
    The data_handler is responsible for filling the Redis database in production.
    For local testing of the dashboard_app alone, this function pre-fills Redis on startup.
    """
    if os.getenv("ENV") != "development":
        return

    pool_balances_data = {
        "ETH/USDC": [
            SwapAmmToken(
                symbol="ETH",
                decimal_factor=Decimal("1E+18"),
                address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                coin_id=None,
                balance_base=166274735523160873935,
                balance_converted=Decimal("166.274735523160873935"),
            ),
            SwapAmmToken(
                symbol="USDC",
                decimal_factor=Decimal("1E+6"),
                address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
                coin_id=None,
                balance_base=702162779844,
                balance_converted=Decimal("702162.779844"),
            ),
        ],
        "DAI/ETH": [
            SwapAmmToken(
                symbol="DAI",
                decimal_factor=Decimal("1E+18"),
                address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
                coin_id=None,
                balance_base=65108606605199470507424,
                balance_converted=Decimal("65108.606605199470507424"),
            ),
            SwapAmmToken(
                symbol="ETH",
                decimal_factor=Decimal("1E+18"),
                address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                coin_id=None,
                balance_base=22016206486065246860,
                balance_converted=Decimal("22.016206486065246860"),
            ),
        ],
        "ETH/USDT": [
            SwapAmmToken(
                symbol="ETH",
                decimal_factor=Decimal("1E+18"),
                address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                coin_id=None,
                balance_base=31901032708597071438,
                balance_converted=Decimal("31.901032708597071438"),
            ),
            SwapAmmToken(
                symbol="USDT",
                decimal_factor=Decimal("1E+6"),
                address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
                coin_id=None,
                balance_base=134678181459,
                balance_converted=Decimal("134678.181459"),
            ),
        ],
        "ETH/wBTC": [
            SwapAmmToken(
                symbol="wBTC",
                decimal_factor=Decimal("1E+8"),
                address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
                coin_id=None,
                balance_base=46905981,
                balance_converted=Decimal("0.46905981"),
            ),
            SwapAmmToken(
                symbol="ETH",
                decimal_factor=Decimal("1E+18"),
                address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
                coin_id=None,
                balance_base=13034136090766330744,
                balance_converted=Decimal("13.034136090766330744"),
            ),
        ],
        "USDT/wBTC": [
            SwapAmmToken(
                symbol="wBTC",
                decimal_factor=Decimal("1E+8"),
                address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
                coin_id=None,
                balance_base=1125739,
                balance_converted=Decimal("0.01125739"),
            ),
            SwapAmmToken(
                symbol="USDT",
                decimal_factor=Decimal("1E+6"),
                address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
                coin_id=None,
                balance_base=1325234363,
                balance_converted=Decimal("1325.234363"),
            ),
        ],
        "DAI/wBTC": [
            SwapAmmToken(
                symbol="DAI",
                decimal_factor=Decimal("1E+18"),
                address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
                coin_id=None,
                balance_base=1385187871194750204052,
                balance_converted=Decimal("1385.187871194750204052"),
            ),
            SwapAmmToken(
                symbol="wBTC",
                decimal_factor=Decimal("1E+8"),
                address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
                coin_id=None,
                balance_base=1630203,
                balance_converted=Decimal("0.01630203"),
            ),
        ],
        "DAI/USDC": [
            SwapAmmToken(
                symbol="DAI",
                decimal_factor=Decimal("1E+18"),
                address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
                coin_id=None,
                balance_base=14505239364029335687970,
                balance_converted=Decimal("14505.239364029335687970"),
            ),
            SwapAmmToken(
                symbol="USDC",
                decimal_factor=Decimal("1E+6"),
                address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
                coin_id=None,
                balance_base=22247672316,
                balance_converted=Decimal("22247.672316"),
            ),
        ],
        "DAI/USDT": [
            SwapAmmToken(
                symbol="DAI",
                decimal_factor=Decimal("1E+18"),
                address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
                coin_id=None,
                balance_base=5328944331027197631074,
                balance_converted=Decimal("5328.944331027197631074"),
            ),
            SwapAmmToken(
                symbol="USDT",
                decimal_factor=Decimal("1E+6"),
                address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
                coin_id=None,
                balance_base=7578909081,
                balance_converted=Decimal("7578.909081"),
            ),
        ],
        "USDC/USDT": [
            SwapAmmToken(
                symbol="USDC",
                decimal_factor=Decimal("1E+6"),
                address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
                coin_id=None,
                balance_base=86819620335,
                balance_converted=Decimal("86819.620335"),
            ),
            SwapAmmToken(
                symbol="USDT",
                decimal_factor=Decimal("1E+6"),
                address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
                coin_id=None,
                balance_base=81397474231,
                balance_converted=Decimal("81397.474231"),
            ),
        ],
        "STRK/USDC": [
            SwapAmmToken(
                symbol="STRK",
                decimal_factor=Decimal("1E+18"),
                address="0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
                coin_id=None,
                balance_base=44947698311457427395814,
                balance_converted=Decimal("44947.698311457427395814"),
            ),
            SwapAmmToken(
                symbol="USDC",
                decimal_factor=Decimal("1E+6"),
                address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
                coin_id=None,
                balance_base=6147176297,
                balance_converted=Decimal("6147.176297"),
            ),
        ],
        "STRK/USDT": [
            SwapAmmToken(
                symbol="STRK",
                decimal_factor=Decimal("1E+18"),
                address="0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
                coin_id=None,
                balance_base=319056783238631116664,
                balance_converted=Decimal("319.056783238631116664"),
            ),
            SwapAmmToken(
                symbol="USDT",
                decimal_factor=Decimal("1E+6"),
                address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
                coin_id=None,
                balance_base=43484094,
                balance_converted=Decimal("43.484094"),
            ),
        ],
        "DAI/STRK": [
            SwapAmmToken(
                symbol="DAI",
                decimal_factor=Decimal("1E+18"),
                address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
                coin_id=None,
                balance_base=14823686402180398360,
                balance_converted=Decimal("14.823686402180398360"),
            ),
            SwapAmmToken(
                symbol="STRK",
                decimal_factor=Decimal("1E+18"),
                address="0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
                coin_id=None,
                balance_base=152246403511055917564,
                balance_converted=Decimal("152.246403511055917564"),
            ),
        ],
    }

    data = {}
    for symbol, pool in pool_balances_data.items():
        for token in pool:
            data[f"{symbol}:{token.address}"] = token.balance_base
    redis_client.set("pool_balances", json.dumps(data))

    # fetch_balance_for_pools()


def get_data(state: State) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
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
    pool_cache = json.loads(
        redis_client.get("pool_balances")
    )
   
    asyncio.run(swap_amm.get_balance_from_cache(pool_cache))
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
    main_chart_data, loans_data = get_data(state=state)  
    for protocol_name in protocols:
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
