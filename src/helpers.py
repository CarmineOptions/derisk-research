import asyncio
import logging
import math
import os
import time
from typing import Iterator, Dict, Set

import google.cloud.storage
import pandas
import requests
import starknet_py.cairo.felt
from starknet_py.net.client_errors import ClientError

import src.blockchain_call
import src.db
import src.settings
import src.types


# TODO: rename
GS_BUCKET_NAME = "derisk-persistent-state/v3"
# Define a constant for the null character that might be present in token symbols
NULL_CHAR = '\x00'




def get_events(
    addresses: tuple[str, ...],
    event_names: tuple[str, ...],
    start_block_number: int = 0,
) -> pandas.DataFrame:
    # TODO: Set up monitoring for new key names. Alert when new key names are found? Holds for all protocols.
    connection = src.db.establish_connection()
    events = pandas.read_sql(
        sql=f"""
            SELECT
                *
            FROM
                starkscan_events
            WHERE
                from_address IN {addresses}
            AND
                key_name IN {event_names}
            AND
                block_number >= {start_block_number}
            ORDER BY
                block_number, id ASC;
        """,
        con=connection,
    )
    connection.close()
    return events.set_index("id")


def float_range(start: float, stop: float, step: float) -> Iterator[float]:
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


# TODO: replace these mappings
UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES = {
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "WBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    "DAI V2": "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad",
}


def load_data(protocol: str) -> tuple[dict[str, pandas.DataFrame], pandas.DataFrame]:
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in src.settings.PAIRS:
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
            main_chart_data[pair] = pandas.read_parquet(
                f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/{underlying_addresses_pair}.parquet",
                engine="fastparquet",
            )
        except FileNotFoundError:
            main_chart_data[pair] = pandas.DataFrame()
    loans_data = pandas.read_parquet(
        f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/loans.parquet",
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
    symbol = await src.blockchain_call.func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return starknet_py.cairo.felt.decode_shortstring(symbol[1])
    return starknet_py.cairo.felt.decode_shortstring(symbol[0])


def get_prices(token_decimals: dict[str, int]) -> dict[str, float]:
    URL = "https://starknet.impulse.avnu.fi/v1/tokens/short"
    response = requests.get(URL)

    if response.ok:
        # Fetch information about tokens.
        tokens_info = response.json()

        prices = {}
        for token, decimals in token_decimals.items():
            token_info = list(
                filter(
                    lambda x: (add_leading_zeros(x["address"]) == token), tokens_info
                )
            )

            # Remove duplicates.
            token_info = [dict(y) for y in {tuple(x.items()) for x in token_info}]

            # Perform sanity checks.
            assert len(token_info) == 1
            assert decimals == token_info[0]["decimals"]

            prices[token] = token_info[0]["currentPrice"]
        return prices
    else:
        response.raise_for_status()


def upload_file_to_bucket(source_path: str, target_path: str):
    bucket_name, folder = GS_BUCKET_NAME.split("/")
    target_path = f"{folder}/{target_path}"

    # Initialize the Google Cloud Storage client with the credentials.
    storage_client = google.cloud.storage.Client.from_service_account_json(
        os.getenv("CREDENTIALS_PATH")
    )

    # Get the target bucket.
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logging.debug(
        f"File = {source_path} uploaded to = gs://{bucket_name}/{target_path}."
    )


def save_dataframe(data: pandas.DataFrame, path: str) -> None:
    directory = path.rstrip(path.split("/")[-1])
    if not directory == "":
        os.makedirs(directory, exist_ok=True)
    data.to_parquet(path, index=False, engine="fastparquet", compression="gzip")
    src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def add_leading_zeros(hash: str) -> str:
    """
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    """
    return "0x" + hash[2:].zfill(64)


def get_addresses(
    token_parameters: src.types.TokenParameters,
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
    token_parameters: src.types.TokenParameters,
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


def get_custom_data(data: pandas.DataFrame) -> list:
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

def extract_token_addresses(loans_data: pandas.DataFrame) -> Set[str]:
    """
    Extracts a set of unique token addresses from the 'Collateral' and 'Debt' columns of a DataFrame.
    
    :param loans_data: A DataFrame containing loan information, with 'Collateral' and 'Debt' columns.
                       Each entry in these columns is expected to be a dictionary where keys are token addresses.
    :return: A set of unique token addresses extracted from both 'Collateral' and 'Debt' dictionaries.
    """
    collateral_addresses = set()
    debt_addresses = set()
    
    for _, row in loans_data.iterrows():
        if isinstance(row['Collateral'], dict):
            collateral_addresses.update(row['Collateral'].keys())
        if isinstance(row['Debt'], dict):
            debt_addresses.update(row['Debt'].keys())
    
    return collateral_addresses.union(debt_addresses)

def update_loan_data_with_symbols(loans_data: pandas.DataFrame, token_symbols: Dict[str, str]) -> pandas.DataFrame:
    """
    Updates the 'Collateral' and 'Debt' columns in the DataFrame to include token symbols next to each token address.
    
    :param loans_data: A DataFrame containing loan information, with 'Collateral' and 'Debt' columns.
                       Each entry in these columns is expected to be a dictionary where keys are token addresses.
    :param token_symbols: A dictionary mapping token addresses to their respective symbols.
    :return: The updated DataFrame with token symbols included in the 'Collateral' and 'Debt' columns.
    """
    def update_column(col):
        if isinstance(col, dict) and col:  # Check if it's a non-empty dictionary
            return {f"{addr} ({token_symbols.get(addr, 'Unknown')})": val for addr, val in col.items()}
        return col  # Return the original value if it's not a non-empty dictionary
    
    loans_data['Collateral'] = loans_data['Collateral'].apply(update_column)
    loans_data['Debt'] = loans_data['Debt'].apply(update_column)
    return loans_data

def fetch_token_symbols_from_set_of_loan_addresses(token_addresses: Set[str]) -> Dict[str, str]:
    """
    Retrieves symbols for a set of token addresses asynchronously.
    
    :param token_addresses: A set of token addresses to retrieve symbols for.
    :return: A dictionary mapping token addresses to their respective symbols.
    """
    async def async_fetch():
        return {addr: await get_underlying_token_symbol(addr) for addr in token_addresses}
    return asyncio.run(async_fetch())

async def get_underlying_token_symbol(token_address: str) -> str | None:
    """
    Retrieves the symbol of the underlying token for a given token address.
    If an underlying asset exists, it fetches its symbol; otherwise, it returns the symbol of the token itself.

    :param token_address: The address of the token to retrieve the symbol for.
    :return: The symbol of the underlying token or the token itself if no underlying asset exists.
    """
    try:
        # Attempt to retrieve the underlying asset's address and its symbol
        underlying_token_address = await src.blockchain_call.func_call(
            addr=token_address,
            selector="underlyingAsset",
            calldata=[],
        )
        underlying_token_address = src.helpers.add_leading_zeros(
            hex(underlying_token_address[0])
        )
        underlying_token_symbol = await src.helpers.get_symbol(
            token_address=underlying_token_address
        )
        return underlying_token_symbol.strip(NULL_CHAR)
    except ClientError as e:
        # Log the network-related error and return 'network_error'
        print(f"Network error while calling contract: {e}")
        return 'network_error'
    except (KeyError, AttributeError, ValueError) as e:
        # Log the specific error if needed
        print(f"Error fetching underlying asset: {e}")
        # If retrieving the underlying asset fails, try returning the symbol of the provided token address
        try:
            underlying_token_symbol = await src.helpers.get_symbol(token_address=token_address)
            return underlying_token_symbol.strip(NULL_CHAR)
        except (KeyError, AttributeError, ValueError) as e:
            # Log the specific error if needed
            print(f"Error fetching token symbol: {e}")
            # If both attempts fail, return "Unknown"
            return "Unknown"