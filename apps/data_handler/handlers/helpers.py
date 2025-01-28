"""
Helper functions for data handling, blockchain interactions, and Google Cloud Storage operations.
"""
import asyncio
import decimal
import logging
import os
from decimal import Decimal
from typing import Iterator

import google.cloud.storage
import pandas
import starknet_py.cairo.felt as cairo_felt_type
from data_handler.handler_tools.constants import TOKEN_MAPPING
from data_handler.handlers import blockchain_call
from data_handler.handlers.settings import PAIRS

from data_handler.db.models import InterestRate
from shared.constants import TOKEN_SETTINGS, ProtocolIDs
from shared.error_handler import BOT
from shared.error_handler.values import MessageTemplates
from shared.custom_types import TokenValues

GS_BUCKET_NAME = "derisk-persistent-state"
ERROR_LOGS = set()
logger = logging.getLogger(__name__)

# TODO: Find a better solution to fix the discrepancies.
# TODO: Update the values.
MAX_ROUNDING_ERRORS: TokenValues = TokenValues(
    values={
        "ETH": decimal.Decimal("0.5e13"),
        "wBTC": decimal.Decimal("1e2"),
        "USDC": decimal.Decimal("1e4"),
        "DAI": decimal.Decimal("1e16"),
        "USDT": decimal.Decimal("1e4"),
        "wstETH": decimal.Decimal("0.5e13"),
        "LORDS": decimal.Decimal("0.5e13"),
        "STRK": decimal.Decimal("0.5e13"),
    },
)


class InterestRateState:
    """Class for storing the state of the interest rate calculation."""

    def __init__(self, current_block: int, last_block_data: InterestRate | None):
        """
        Initialize the InterestRateState object.
        :param current_block: int - The current block number.
        :param last_block_data: InterestRate | None - 
        The last block data from storage or None if is not present.
        """
        self.last_block_data = last_block_data
        self.current_block = current_block
        self.current_timestamp = last_block_data.timestamp if last_block_data else 0

        self.cumulative_collateral_interest_rates: dict[str, Decimal] = {}
        self.cumulative_debt_interest_rate: dict[str, Decimal] = {}
        self.previous_token_timestamps: dict[str, int] = {}
        self._fill_state_data()

    def get_seconds_passed(self, token_name: str) -> Decimal:
        """
        Get the number of seconds passed since the last event for given token.
        :param token_name: str - The name of the token, for example `STRK`.
        :return: Decimal - The number of seconds passed.
        """
        return Decimal(self.current_timestamp - self.previous_token_timestamps[token_name])

    def update_state_cumulative_data(
        self,
        token_name: str,
        current_block: int,
        cumulative_collateral_interest_rate_increase: Decimal,
        cumulative_debt_interest_rate_increase: Decimal,
    ) -> None:
        """
        Update the state of interest rate calculation with the new data.
        :param token_name: str - The name of the token, for example `STRK`.
        :param current_block: int - The current block number.
        :param cumulative_collateral_interest_rate_increase: 
        Decimal - The change in collateral(supply) interest rate.
        :param cumulative_debt_interest_rate_increase: 
        Decimal - The change in debt(borrow) interest rate.
        """
        self.cumulative_collateral_interest_rates[token_name
                                                  ] += cumulative_collateral_interest_rate_increase
        self.cumulative_debt_interest_rate[token_name] += cumulative_debt_interest_rate_increase
        self.previous_token_timestamps[token_name] = self.current_timestamp
        self.current_block = current_block

    def _fill_state_data(self) -> None:
        """General function for filling the state data."""
        self._fill_cumulative_data()
        self._fill_timestamps()

    def _fill_cumulative_data(self) -> None:
        """Fill the cumulative collateral and debt data with latest block data or default values. 
        Default value is 1."""
        if self.last_block_data:
            (
                self.cumulative_collateral_interest_rates,
                self.cumulative_debt_interest_rate,
            ) = self.last_block_data.get_json_deserialized()
        else:
            self.cumulative_collateral_interest_rates = {
                token_name: Decimal("1")
                for token_name in TOKEN_MAPPING.values()
            }
            self.cumulative_debt_interest_rate = (self.cumulative_collateral_interest_rates.copy())

    def _fill_timestamps(self) -> None:
        """Fill the token timestamps with latest block timestamp or default value. 
        Default value is 0"""
        if self.last_block_data:
            self.previous_token_timestamps = {
                token_name: self.last_block_data.timestamp
                for token_name in TOKEN_MAPPING.values()
            }
        else:
            # First token event occurrence will update the timestamp,
            # so after first interest rate for token will be 1.
            self.previous_token_timestamps = {
                token_name: 0
                for token_name in TOKEN_MAPPING.values()
            }

    def build_interest_rate_model(self, protocol_id: ProtocolIDs) -> InterestRate:
        """
        Build the InterestRate model object from the current state data.
        :param protocol_id: ProtocolIDs - The ID of protocol.
        :return: InterestRate - The InterestRate model object.
        """
        return InterestRate(
            block=self.current_block,
            timestamp=self.current_timestamp,
            protocol_id=protocol_id,
            **self._serialize_cumulative_data(),
        )

    def _serialize_cumulative_data(self) -> dict[str, dict[str, str]]:
        """Serialize the cumulative collateral and debt data to write to the database."""
        collateral = {
            token_name: str(value)
            for token_name, value in self.cumulative_collateral_interest_rates.items()
        }
        debt = {
            token_name: str(value)
            for token_name, value in self.cumulative_debt_interest_rate.items()
        }
        return {"collateral": collateral, "debt": debt}


def decimal_range(start: decimal.Decimal, stop: decimal.Decimal,
                  step: decimal.Decimal) -> Iterator[decimal.Decimal]:
    """
    Generates a range of decimals from start to stop with a given step.
    """
    while start < stop:
        yield start
        start += step


def get_range(start: decimal.Decimal, stop: decimal.Decimal,
              step: decimal.Decimal) -> list[decimal.Decimal]:
    """
    Returns a list of decimal values from start to stop with a specified step.
    """
    return [x for x in decimal_range(start=start, stop=stop, step=step)]


def get_collateral_token_range(
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
) -> list[decimal.Decimal]:
    """
    Returns a range of collateral token values based on price and token type.
    """
    assert collateral_token in {"ETH", "wBTC", "STRK"}
    TOKEN_STEP = {
        "ETH": decimal.Decimal("50"),
        "wBTC": decimal.Decimal("500"),
        "STRK": decimal.Decimal("0.05"),
    }
    return get_range(
        start=TOKEN_STEP[collateral_token],
        stop=collateral_token_price * decimal.Decimal("1.2"),
        step=TOKEN_STEP[collateral_token],
    )


def load_data(
    protocol: str,
) -> tuple[dict[str, pandas.DataFrame], pandas.DataFrame, pandas.DataFrame]:
    """
    Loads data for a specified protocol from Google Cloud Storage as DataFrames.
    """
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in PAIRS:
        main_chart_data[pair] = pandas.read_parquet(
            f"gs://{GS_BUCKET_NAME}/{directory}/{pair}.parquet"
        )
    histogram_data = pandas.read_parquet(f"gs://{GS_BUCKET_NAME}/{directory}/histogram.parquet")
    loans_data = pandas.read_parquet(f"gs://{GS_BUCKET_NAME}/{directory}/loans.parquet")
    return (
        main_chart_data,
        histogram_data,
        loans_data,
    )


# TODO: Improve this.
def get_symbol(address: str, protocol: str | None = None) -> str:
    """
    Get the symbol of the token by its address.

    This function takes an address and an optional protocol as input, 
    and returns the symbol of the token.
    If the address is not found in the symbol table, it raises a KeyError.
    If a protocol is provided and the address is not found, 
    it also sends an error message to a Telegram bot.

    :param address: str - The address of the token.
    :param protocol: str | None - The name of the protocol.
    :return: str - The symbol of the token.
    :raises KeyError: If the address is not found in the symbol table.
    :note: If the address is not found and a protocol is provided, 
    an error message will be sent to a Telegram bot.

    """
    # A tuple of that always has this order: `address`, `protocol`.
    error_info = (address, protocol)
    # you can match addresses as numbers
    n = int(address, base=16)
    symbol_address_map = {
        token: token_settings.address
        for token, token_settings in TOKEN_SETTINGS.items()
    }
    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol

    if protocol and error_info not in ERROR_LOGS:
        ERROR_LOGS.update({error_info})
        asyncio.run(
            BOT.send_message(
                MessageTemplates.NEW_TOKEN_MESSAGE.format(protocol_name=protocol, address=address)
            )
        )

    raise KeyError(f"Address = {address} does not exist in the symbol table.")


async def get_async_symbol(token_address: str) -> str:
    """
    Retrieves the symbol of a token asynchronously by its address.
    """
    # DAI V2's symbol is `DAI` but we don't want to mix it with DAI = DAI V1.
    if (token_address == "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad"):
        return "DAI V2"
    symbol = await blockchain_call.func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return cairo_felt_type.decode_shortstring(symbol[1])
    return cairo_felt_type.decode_shortstring(symbol[0])


def upload_file_to_bucket(source_path: str, target_path: str) -> None:
    """
    Upload file to bucket
    :param source_path: source path
    :param target_path: target path
    :return: None
    """
    # Initialize the Google Cloud Storage client with the credentials.
    try:
        # Initialize the Google Cloud Storage client with the credentials.
        storage_client = google.cloud.storage.Client.from_service_account_json(
            # It can run only if CREDENTIALS_PATH=<value> or CREDENTIALS_PATH=""
            os.getenv("CREDENTIALS_PATH", "")
        )
    except FileNotFoundError as e:
        logger.info(f"Failed to initialize the Google Cloud Storage client due to an error: {e}")
        raise FileNotFoundError

    # Get the target bucket.
    bucket = storage_client.bucket(GS_BUCKET_NAME)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logger.info(f"File = {source_path} uploaded to = gs://{GS_BUCKET_NAME}/{target_path}")


def save_dataframe(data: pandas.DataFrame, path: str) -> None:
    """
    Saves a DataFrame to a local file, uploads it to Google Cloud Storage, and
      deletes the local file.
    """
    directory = path.rstrip(path.split("/")[-1])
    if not directory == "":
        os.makedirs(directory, exist_ok=True)
    data.to_parquet(path, index=False, engine="fastparquet", compression="gzip")
    upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def get_addresses(
    token_parameters: "TokenParameters",
    underlying_address: str | None = None,
    underlying_symbol: str | None = None,
) -> list[str]:
    """
    Get the addresses of the tokens based on the underlying address or symbol.
    :param token_parameters: the token parameters
    :param underlying_address: underlying address
    :param underlying_symbol: underlying symbol
    :return: list of addresses
    """
    # Up to 2 addresses can match the given `underlying_address` or `underlying_symbol`.
    if underlying_address:
        addresses = [
            x.address for x in token_parameters.values()
            if x.underlying_address == underlying_address
        ]
    elif underlying_symbol:
        addresses = [
            x.address for x in token_parameters.values() if x.underlying_symbol == underlying_symbol
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
