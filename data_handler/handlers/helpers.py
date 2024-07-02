import decimal
import os
from decimal import Decimal
from typing import Iterator, Optional, Union

import google.cloud.storage
import pandas

from handler_tools.constants import TOKEN_MAPPING, ProtocolIDs
from db.models import InterestRate
from handlers.settings import TOKEN_SETTINGS, PAIRS

GS_BUCKET_NAME = "derisk-persistent-state"


class TokenValues:
    def __init__(
        self,
        values: Optional[dict[str, Union[bool, decimal.Decimal]]] = None,
        # TODO: Only one parameter should be specified..
        init_value: decimal.Decimal = decimal.Decimal("0"),
    ) -> None:
        if values:
            # Nostra Mainnet can contain different tokens that aren't mentioned in `TOKEN_SETTINGS`
            # assert set(values.keys()) == set(TOKEN_SETTINGS.keys())
            self.values: dict[str, decimal.Decimal] = values
        else:
            self.values: dict[str, decimal.Decimal] = {
                token: init_value for token in TOKEN_SETTINGS
            }


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


class ExtraInfo:
    block: int
    timestamp: int


class Portfolio(TokenValues):
    """A class that describes holdings of tokens."""

    MAX_ROUNDING_ERRORS: TokenValues = MAX_ROUNDING_ERRORS

    def __init__(self) -> None:
        super().__init__(init_value=decimal.Decimal("0"))

    def round_small_value_to_zero(self, token: str):
        if (
            -self.MAX_ROUNDING_ERRORS.values[token]
            < self.values[token]
            < self.MAX_ROUNDING_ERRORS.values[token]
        ):
            self.values[token] = decimal.Decimal("0")

    def increase_value(self, token: str, value: decimal.Decimal):
        self.values[token] += value
        self.round_small_value_to_zero(token=token)

    def set_value(self, token: str, value: decimal.Decimal):
        self.values[token] = value
        self.round_small_value_to_zero(token=token)


class InterestRateState:
    """Class for storing the state of the interest rate calculation."""

    def __init__(self, current_block: int, last_block_data: InterestRate | None):
        """
        Initialize the InterestRateState object.
        :param current_block: int - The current block number.
        :param last_block_data: InterestRate | None - The last block data from storage or None if is not present.
        """
        self.last_block_data = last_block_data
        self.current_block = current_block
        self.latest_timestamp = last_block_data.timestamp if last_block_data else 0

        self.cumulative_collateral_interest_rates: dict[str, Decimal] = {}
        self.cumulative_debt_interest_rate: dict[str, Decimal] = {}
        self.token_timestamps: dict[str, int] = {}
        self._fill_state_data()

    def get_seconds_passed(self, token_name: str) -> Decimal:
        """
        Get the number of seconds passed since the last event for given token.
        :param token_name: str - The name of the token, for example `STRK`.
        :return: Decimal - The number of seconds passed.
        """
        return Decimal(
            self.latest_timestamp - self.token_timestamps[token_name]
        )

    def update_state_cumulative_data(
            self, token_name: str, current_block: int, collateral_increase: Decimal, debt_increase: Decimal
    ) -> None:
        """
        Update the state of interest rate calculation with the new data.
        :param token_name: str - The name of the token, for example `STRK`.
        :param current_block: int - The current block number.
        :param collateral_increase: Decimal - The change in collateral(supply) interest rate.
        :param debt_increase: Decimal - The change in debt(borrow) interest rate.
        """
        self.cumulative_collateral_interest_rates[token_name] += collateral_increase
        self.cumulative_debt_interest_rate[token_name] += debt_increase
        self.token_timestamps[token_name] = self.latest_timestamp
        self.current_block = current_block

    def _fill_state_data(self) -> None:
        """General function for filling the state data."""
        self._fill_cumulative_data()
        self._fill_timestamps()

    def _fill_cumulative_data(self) -> None:
        """Fill the cumulative collateral and debt data with latest block data or default values. Default value is 1."""
        if self.last_block_data:
            self.cumulative_collateral_interest_rates, self.cumulative_debt_interest_rate = (
                self.last_block_data.get_json_deserialized()
            )
        else:
            self.cumulative_collateral_interest_rates = {
                token_name: Decimal("1") for token_name in TOKEN_MAPPING.values()
            }
            self.cumulative_debt_interest_rate = self.cumulative_collateral_interest_rates.copy()

    def _fill_timestamps(self) -> None:
        """Fill the token timestamps with latest block timestamp or default value. Default value is 0"""
        if self.last_block_data:
            self.token_timestamps = {
                token_name: self.last_block_data.timestamp for token_name in TOKEN_MAPPING.values()
            }
        else:
            # First token event occurrence will update the timestamp,
            # so after first interest rate for token will be 1.
            self.token_timestamps = {
                token_name: 0 for token_name in TOKEN_MAPPING.values()
            }

    def build_interest_rate_model(self, protocol_id: ProtocolIDs) -> InterestRate:
        """
        Build the InterestRate model object from the current state data.
        :param protocol_id: ProtocolIDs - The ID of protocol.
        :return: InterestRate - The InterestRate model object.
        """
        return InterestRate(
            block=self.current_block,
            timestamp=self.latest_timestamp,
            protocol_id=protocol_id,
            **self._serialize_cumulative_data()
        )

    def _serialize_cumulative_data(self) -> dict[str, dict[str, str]]:
        """Serialize the cumulative collateral and debt data to write to the database."""
        collateral = {
            token_name: str(value) for token_name, value in self.cumulative_collateral_interest_rates.items()
        }
        debt = {
            token_name: str(value) for token_name, value in self.cumulative_debt_interest_rate.items()
        }
        return {"collateral": collateral, "debt": debt}


def decimal_range(
    start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal
) -> Iterator[decimal.Decimal]:
    while start < stop:
        yield start
        start += step


def get_range(
    start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal
) -> list[decimal.Decimal]:
    return [x for x in decimal_range(start=start, stop=stop, step=step)]


def get_collateral_token_range(
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
) -> list[decimal.Decimal]:
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
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in PAIRS:
        main_chart_data[pair] = pandas.read_parquet(
            f"gs://{GS_BUCKET_NAME}/{directory}/{pair}.parquet"
        )
    histogram_data = pandas.read_parquet(
        f"gs://{GS_BUCKET_NAME}/{directory}/histogram.parquet"
    )
    loans_data = pandas.read_parquet(f"gs://{GS_BUCKET_NAME}/{directory}/loans.parquet")
    return (
        main_chart_data,
        histogram_data,
        loans_data,
    )


# TODO: Improve this.
def get_symbol(address: str) -> str:
    # you can match addresses as numbers
    n = int(address, base=16)
    symbol_address_map = {
        token: token_settings.address
        for token, token_settings in TOKEN_SETTINGS.items()
    }
    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol
    raise KeyError(f"Address = {address} does not exist in the symbol table.")


def upload_file_to_bucket(source_path: str, target_path: str):
    # Initialize the Google Cloud Storage client with the credentials.
    storage_client = google.cloud.storage.Client.from_service_account_json(
        os.getenv("CREDENTIALS_PATH")
    )

    # Get the target bucket.
    bucket = storage_client.bucket(GS_BUCKET_NAME)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    print(f"File = {source_path} uploaded to = gs://{GS_BUCKET_NAME}/{target_path}")


def save_dataframe(data: pandas.DataFrame, path: str) -> None:
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
