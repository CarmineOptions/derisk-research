import logging
import math
import os
from typing import Iterator

import pandas as pd
import requests
from google.cloud.storage import Client
from shared.blockchain_call import func_call
from shared.constants import TOKEN_SETTINGS
from shared.types import TokenParameters
from starknet_py.cairo.felt import decode_shortstring

from dashboard_app.helpers.settings import (
    PAIRS,
    UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES,
)

GS_BUCKET_NAME = "derisk-persistent-state/v3"


def float_range(start: float, stop: float, step: float) -> Iterator[float]:
    """
    Generator that yields float values within the specified range.

    :param start: Start of the range.
    :param stop: End of the range.
    :param step: Step size.
    :return: Generator of float values.
    """
    while start < stop:
        yield start
        start += step


def get_collateral_token_range(
    collateral_token_underlying_address: str,
    collateral_token_price: float,
) -> list[float]:
    TARGET_NUMBER_OF_VALUES = 50
    start_price = 0.0
    stop_price = collateral_token_price * 1.2
    # Calculate rough step size to get about 50 (target) values
    raw_step_size = (stop_price - start_price) / TARGET_NUMBER_OF_VALUES
    # Round the step size to the closest readable value (1, 2, or 5 times powers of 10)
    magnitude = 10 ** math.floor(math.log10(raw_step_size))  # Base scale
    step_factors = [1, 2, 2.5, 5, 10]
    difference = [
        abs(50 - stop_price / (k * magnitude)) for k in step_factors
    ]  # Stores the difference between the target value and number of values generated from each step factor.
    readable_step = (
        step_factors[difference.index(min(difference))] * magnitude
    )  # Gets readable step from step factor with values closest to the target value.

    # Generate values using the calculated readable step
    return list(float_range(start=readable_step, stop=stop_price, step=readable_step))


def load_data(protocol: str) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in PAIRS:
        collateral_token_underlying_symbol, debt_token_underlying_symbol = pair.split(
            "-"
        )
        collateral_token_underlying_address = (
            UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[
                collateral_token_underlying_symbol
            ]
        )
        debt_token_underlying_address = UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[
            debt_token_underlying_symbol
        ]
        underlying_addresses_pair = (
            f"{collateral_token_underlying_address}-{debt_token_underlying_address}"
        )
        try:
            main_chart_data[pair] = pd.read_parquet(
                f"gs://{GS_BUCKET_NAME}/{directory}/{underlying_addresses_pair}.parquet",
                engine="fastparquet",
            )
        except FileNotFoundError:
            main_chart_data[pair] = pd.DataFrame()
    loans_data = pd.read_parquet(
        f"gs://{GS_BUCKET_NAME}/{directory}/loans.parquet",
        engine="fastparquet",
    )
    return main_chart_data, loans_data


async def get_symbol(token_address: str) -> str:
    # DAI V2's symbol is `DAI` but we don't want to mix it with DAI = DAI V1.
    if (
        token_address
        == "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad"
    ):
        return "DAI V2"
    symbol = await func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return decode_shortstring(symbol[1])
    return decode_shortstring(symbol[0])


def get_prices(token_decimals: dict[str, int]) -> dict[str, float]:
    """
    Get the prices of the tokens.
    :param token_decimals: Token decimals.
    :return: Dict with token addresses as keys and token prices as values.
    """
    URL = "https://starknet.impulse.avnu.fi/v1/tokens/short"
    response = requests.get(URL)

    if not response.ok:
        response.raise_for_status()

    tokens_info = response.json()

    # Define the addresses for which you do not want to apply add_leading_zeros
    skip_leading_zeros_addresses = {
        TOKEN_SETTINGS["STRK"].address,
    }

    # Create a map of token addresses to token information, applying add_leading_zeros conditionally
    token_info_map = {
        (
            token["address"]
            if token["address"] in skip_leading_zeros_addresses
            else add_leading_zeros(token["address"])
        ): token
        for token in tokens_info
    }

    prices = {}
    for token, decimals in token_decimals.items():
        token_info = token_info_map.get(token)

        if not token_info:
            logging.error(f"Token {token} not found in response.")
            continue

        if decimals != token_info.get("decimals"):
            logging.error(
                f"Decimal mismatch for token {token}: expected {decimals}, got {token_info.get('decimals')}"
            )
            continue

        prices[token] = token_info.get("currentPrice")

    return prices


def upload_file_to_bucket(source_path: str, target_path: str):
    bucket_name, folder = GS_BUCKET_NAME.split("/")
    target_path = f"{folder}/{target_path}"

    # Initialize the Google Cloud Storage client with the credentials.
    storage_client = Client.from_service_account_json(os.getenv("CREDENTIALS_PATH", ""))

    # Get the target bucket.
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logging.debug(
        f"File = {source_path} uploaded to = gs://{bucket_name}/{target_path}."
    )


def save_dataframe(data: pd.DataFrame, path: str) -> None:
    directory = path.rstrip(path.split("/")[-1])
    if not directory == "":
        os.makedirs(directory, exist_ok=True)
    data.to_parquet(path, index=False, engine="fastparquet", compression="gzip")
    upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def add_leading_zeros(hash: str) -> str:
    """
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    """
    return "0x" + hash[2:].zfill(64)


def get_addresses(
    token_parameters: TokenParameters,
    underlying_address: str | None = None,
    underlying_symbol: str | None = None,
) -> list[str]:
    # Up to 2 addresses can match the given `underlying_address` or `underlying_symbol`.
    if underlying_address:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_address == underlying_address
        ]
    elif underlying_symbol:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_symbol == underlying_symbol
        ]
    else:
        raise ValueError(
            "Both `underlying_address` =  {} or `underlying_symbol` = {} are not specified.".format(
                underlying_address,
                underlying_symbol,
            )
        )
    assert len(addresses) <= 2
    return addresses


def get_underlying_address(
    token_parameters: TokenParameters,
    underlying_symbol: str,
) -> str:
    # One underlying address at maximum can match the given `underlying_symbol`.
    underlying_addresses = {
        x.underlying_address
        for x in token_parameters.values()
        if x.underlying_symbol == underlying_symbol
    }
    if not underlying_addresses:
        return ""
    assert len(underlying_addresses) == 1
    return list(underlying_addresses)[0]


def get_custom_data(data: pd.DataFrame) -> list:
    """
    Returns custom data for Plotly charts.
    :param data: dataframe
    :return: list
    """
    custom_columns = [
        "liquidable_debt_at_interval",
        "liquidable_debt_at_interval_zkLend",
        "liquidable_debt_at_interval_Nostra Alpha",
        "liquidable_debt_at_interval_Nostra Mainnet",
    ]
    customdata = []
    data_length = len(data)
    for col in custom_columns:
        if col in data.columns:
            customdata.append(data[col].values)
        else:
            customdata.append([0] * data_length)  # Use 0 if the column is missing

    # Transpose customdata to match rows to records
    customdata = list(zip(*customdata))

    return customdata
