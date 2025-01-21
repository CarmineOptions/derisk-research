import asyncio
import logging
from typing import Dict, Set

import pandas as pd
import starknet_py
from data_handler.handlers.blockchain_call import func_call
from starknet_py.net.client_errors import ClientError

from .constants import GS_BUCKET_NAME, NULL_CHAR, PAIRS, UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def add_leading_zeros(hash: str) -> str:
    """
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    """
    return "0x" + hash[2:].zfill(64)


def load_data(protocol: str) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Loads data from `protocol`
    Args:
        protocol: str

    Returns: tuple[dict[str, pd.DataFrame], pd.DataFrame]

    """
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in PAIRS:
        collateral_token_underlying_symbol, debt_token_underlying_symbol = pair.split("-")
        collateral_token_underlying_address = UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES[
            collateral_token_underlying_symbol
        ]
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


def extract_token_addresses(loans_data: pd.DataFrame) -> Set[str]:
    """
    Extracts a set of unique token addresses from the 'Collateral' and 'Debt' columns of a DataFrame.

    :param loans_data: A DataFrame containing loan information, with 'Collateral' and 'Debt' columns.
                       Each entry in these columns is expected to be a dictionary where keys are token addresses.
    :return: A set of unique token addresses extracted from both 'Collateral' and 'Debt' dictionaries.
    """
    collateral_addresses = set()
    debt_addresses = set()

    for _, row in loans_data.iterrows():
        if isinstance(row["Collateral"], dict):
            collateral_addresses.update(row["Collateral"].keys())
        if isinstance(row["Debt"], dict):
            debt_addresses.update(row["Debt"].keys())

    return collateral_addresses.union(debt_addresses)


async def get_symbol(token_address: str) -> str:
    """
    Retrieves the symbol associated with a token address.
    Args:
        token_address: str

    Returns: str

    """
    # DAI V2's symbol is `DAI` but we don't want to mix it with DAI = DAI V1.
    if token_address == "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad":
        return "DAI V2"
    symbol = await func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return starknet_py.cairo.felt.decode_shortstring(symbol[1])
    return starknet_py.cairo.felt.decode_shortstring(symbol[0])


async def get_underlying_token_symbol(token_address: str) -> str | None:
    """
    Retrieves the symbol of the underlying token for a given token address.
    If an underlying asset exists, it fetches its symbol; otherwise, it returns the symbol of the token itself.

    :param token_address: The address of the token to retrieve the symbol for.
    :return: The symbol of the underlying token or the token itself if no underlying asset exists.
    """
    try:
        # Attempt to retrieve the underlying asset's address and its symbol
        underlying_token_address = await func_call(
            addr=token_address,
            selector="underlyingAsset",
            calldata=[],
        )
        underlying_token_address = add_leading_zeros(hex(underlying_token_address[0]))
        underlying_token_symbol = await get_symbol(token_address=underlying_token_address)
        return underlying_token_symbol.strip(NULL_CHAR)
    except ClientError as e:
        # Log the network-related error and return 'network_error'
        logger.info(f"Network error while calling contract: {e}")
        return "network_error"
    except (KeyError, AttributeError, ValueError) as e:
        # Log the specific error if needed
        logger.info(f"Error fetching underlying asset: {e}")
        # If retrieving the underlying asset fails, try returning the symbol of the provided token address
        try:
            underlying_token_symbol = await get_symbol(token_address=token_address)
            return underlying_token_symbol.strip(NULL_CHAR)
        except (KeyError, AttributeError, ValueError) as e:
            # Log the specific error if needed
            logger.info(f"Error fetching token symbol: {e}")
            # If both attempts fail, return "Unknown"
            return "Unknown"


def update_loan_data_with_symbols(
    loans_data: pd.DataFrame, token_symbols: Dict[str, str]
) -> pd.DataFrame:
    """
    Updates the 'Collateral' and 'Debt' columns in the DataFrame to include token symbols next to each token address.

    :param loans_data: A DataFrame containing loan information, with 'Collateral' and 'Debt' columns.
                       Each entry in these columns is expected to be a dictionary where keys are token addresses.
    :param token_symbols: A dictionary mapping token addresses to their respective symbols.
    :return: The updated DataFrame with token symbols included in the 'Collateral' and 'Debt' columns.
    """

    def update_column(col: pd.DataFrame) -> dict | pd.DataFrame:
        """
        Updates the 'Collateral' and 'Debt' columns in the DataFrame.
        Args:
            col: dict mapping token addresses to their respective symbols.

        Returns: dict | pd.DataFrame

        """
        if isinstance(col, dict) and col:  # Check if it's a non-empty dictionary
            return {
                f"{addr} ({token_symbols.get(addr, 'Unknown')})": val for addr, val in col.items()
            }
        return col  # Return the original value if it's not a non-empty dictionary

    loans_data["Collateral"] = loans_data["Collateral"].apply(update_column)
    loans_data["Debt"] = loans_data["Debt"].apply(update_column)
    return loans_data


def fetch_token_symbols_from_set_of_loan_addresses(
    token_addresses: Set[str],
) -> Dict[str, str]:
    """
    Retrieves symbols for a set of token addresses asynchronously.

    :param token_addresses: A set of token addresses to retrieve symbols for.
    :return: A dictionary mapping token addresses to their respective symbols.
    """

    async def async_fetch() -> dict:
        """
        Fetches symbols for a set of token addresses asynchronously.
        Returns: dict mapping token addresses to their respective symbols.
        """
        return {addr: await get_underlying_token_symbol(addr) for addr in token_addresses}

    return asyncio.run(async_fetch())
