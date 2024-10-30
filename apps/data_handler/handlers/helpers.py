"""Helper functions and classes for data handling and token management.

This module provides utilities for managing interest rate calculations,
token data loading, and Google Cloud Storage interactions.
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
from shared.types import TokenValues

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
        """Initialize the InterestRateState object.

        Args:
            current_block: The current block number.
            last_block_data: The last block data from storage or None if not present.
        """
        self.last_block_data = last_block_data
        self.current_block = current_block
        self.current_timestamp = last_block_data.timestamp if last_block_data else 0

        self.cumulative_collateral_interest_rates: dict[str, Decimal] = {}
        self.cumulative_debt_interest_rate: dict[str, Decimal] = {}
        self.previous_token_timestamps: dict[str, int] = {}
        self._fill_state_data()

    def get_seconds_passed(self, token_name: str) -> Decimal:
        """Get the number of seconds passed since the last event for given token.

        Args:
            token_name: The name of the token, for example `STRK`.

        Returns:
            The number of seconds passed.
        """
        return Decimal(self.current_timestamp - self.previous_token_timestamps[token_name])

    def update_state_cumulative_data(
        self,
        token_name: str,
        current_block: int,
        cumulative_collateral_interest_rate_increase: Decimal,
        cumulative_debt_interest_rate_increase: Decimal,
    ) -> None:
        """Update the state of interest rate calculation with the new data.

        Args:
            token_name: The name of the token, for example `STRK`.
            current_block: The current block number.
            cumulative_collateral_interest_rate_increase: The change in collateral interest rate.
            cumulative_debt_interest_rate_increase: The change in debt interest rate.
        """
        self.cumulative_collateral_interest_rates[
            token_name
        ] += cumulative_collateral_interest_rate_increase
        self.cumulative_debt_interest_rate[token_name] += cumulative_debt_interest_rate_increase
        self.previous_token_timestamps[token_name] = self.current_timestamp
        self.current_block = current_block

    def _fill_state_data(self) -> None:
        """Fill the state data with initial values."""
        self._fill_cumulative_data()
        self._fill_timestamps()

    def _fill_cumulative_data(self) -> None:
        """Fill cumulative collateral and debt data with latest block data or defaults."""
        if self.last_block_data:
            (
                self.cumulative_collateral_interest_rates,
                self.cumulative_debt_interest_rate,
            ) = self.last_block_data.get_json_deserialized()
        else:
            default_value = {token_name: Decimal("1") for token_name in TOKEN_MAPPING.values()}
            self.cumulative_collateral_interest_rates = default_value
            self.cumulative_debt_interest_rate = default_value.copy()

    def _fill_timestamps(self) -> None:
        """Fill token timestamps with latest block timestamp or default value 0."""
        if self.last_block_data:
            self.previous_token_timestamps = {
                token_name: self.last_block_data.timestamp for token_name in TOKEN_MAPPING.values()
            }
        else:
            self.previous_token_timestamps = {
                token_name: 0 for token_name in TOKEN_MAPPING.values()
            }

    def build_interest_rate_model(self, protocol_id: ProtocolIDs) -> InterestRate:
        """Build the InterestRate model object from the current state data.

        Args:
            protocol_id: The ID of protocol.

        Returns:
            The InterestRate model object.
        """
        return InterestRate(
            block=self.current_block,
            timestamp=self.current_timestamp,
            protocol_id=protocol_id,
            **self._serialize_cumulative_data(),
        )

    def _serialize_cumulative_data(self) -> dict[str, dict[str, str]]:
        """Serialize the cumulative collateral and debt data for database storage."""
        collateral = {
            token_name: str(value)
            for token_name, value in self.cumulative_collateral_interest_rates.items()
        }
        debt = {
            token_name: str(value)
            for token_name, value in self.cumulative_debt_interest_rate.items()
        }
        return {"collateral": collateral, "debt": debt}


def decimal_range(
    start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal
) -> Iterator[decimal.Decimal]:
    """Generate a range of decimal numbers.

    Args:
        start: Starting value
        stop: End value (exclusive)
        step: Step size

    Yields:
        Next decimal value in the sequence
    """
    while start < stop:
        yield start
        start += step


def get_range(
    start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal
) -> list[decimal.Decimal]:
    """Get a list of decimal numbers within a range.

    Args:
        start: Starting value
        stop: End value (exclusive)
        step: Step size

    Returns:
        List of decimal values
    """
    return list(decimal_range(start=start, stop=stop, step=step))


def get_collateral_token_range(
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
) -> list[decimal.Decimal]:
    """Get the range of values for a collateral token.

    Args:
        collateral_token: Token symbol
        collateral_token_price: Current token price

    Returns:
        List of decimal values representing the token range
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
    """Load protocol data from GCS storage.

    Args:
        protocol: Protocol name

    Returns:
        Tuple containing main chart data, histogram data, and loans data
    """
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {
        pair: pandas.read_parquet(f"gs://{GS_BUCKET_NAME}/{directory}/{pair}.parquet")
        for pair in PAIRS
    }
    histogram_data = pandas.read_parquet(f"gs://{GS_BUCKET_NAME}/{directory}/histogram.parquet")
    loans_data = pandas.read_parquet(f"gs://{GS_BUCKET_NAME}/{directory}/loans.parquet")
    return main_chart_data, histogram_data, loans_data


def get_symbol(address: str, protocol: str | None = None) -> str:
    """Get the symbol of the token by its address.

    Args:
        address: The address of the token
        protocol: Optional protocol name for error reporting

    Returns:
        Token symbol

    Raises:
        KeyError: If address not found in symbol table
    """
    error_info = (address, protocol)
    n = int(address, base=16)
    symbol_address_map = {
        token: token_settings.address for token, token_settings in TOKEN_SETTINGS.items()
    }

    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol

    if protocol and error_info not in ERROR_LOGS:
        ERROR_LOGS.update({error_info})
        msg = MessageTemplates.NEW_TOKEN_MESSAGE.format(protocol_name=protocol, address=address)
        asyncio.run(BOT.send_message(msg))

    raise KeyError(f"Address = {address} does not exist in the symbol table.")


async def get_async_symbol(token_address: str) -> str:
    """Get token symbol asynchronously from blockchain.

    Args:
        token_address: Token contract address

    Returns:
        Token symbol as string
    """
    # Special case for DAI V2
    if token_address == ("0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad"):
        return "DAI V2"

    symbol = await blockchain_call.func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # Handle multi-value return
    if len(symbol) > 1:
        return cairo_felt_type.decode_shortstring(symbol[1])
    return cairo_felt_type.decode_shortstring(symbol[0])


def upload_file_to_bucket(source_path: str, target_path: str) -> None:
    """Upload file to Google Cloud Storage bucket.

    Args:
        source_path: Local file path
        target_path: Target path in bucket

    Raises:
        FileNotFoundError: If credentials file not found
    """
    try:
        storage_client = google.cloud.storage.Client.from_service_account_json(
            os.getenv("CREDENTIALS_PATH", "")
        )
    except FileNotFoundError as e:
        logger.info(f"Failed to initialize storage client: {e}")
        raise

    bucket = storage_client.bucket(GS_BUCKET_NAME)
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logger.info(f"File {source_path} uploaded to gs://{GS_BUCKET_NAME}/{target_path}")


def save_dataframe(data: pandas.DataFrame, path: str) -> None:
    """Save DataFrame to parquet file and upload to GCS bucket.

    Args:
        data: pandas DataFrame to save
        path: Target file path
    """
    directory = path.rstrip(path.split("/")[-1])
    if directory:
        os.makedirs(directory, exist_ok=True)
    data.to_parquet(path, index=False, engine="fastparquet", compression="gzip")
    upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def get_addresses(
    token_parameters: "TokenParameters",
    underlying_address: str | None = None,
    underlying_symbol: str | None = None,
) -> list[str]:
    """Get token addresses based on underlying address or symbol.

    Args:
        token_parameters: Token parameters object
        underlying_address: Optional underlying token address
        underlying_symbol: Optional underlying token symbol

    Returns:
        List of matching token addresses

    Raises:
        ValueError: If neither address nor symbol provided
    """
    if underlying_address:
        addresses = [
            x.address
            for x in token_parameters.values()
            if x.underlying_address == underlying_address
        ]
    elif underlying_symbol:
        addresses = [
            x.address for x in token_parameters.values() if x.underlying_symbol == underlying_symbol
        ]
    else:
        raise ValueError("Neither underlying_address nor underlying_symbol specified")
    assert len(addresses) <= 2
    return addresses
