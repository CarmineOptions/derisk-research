from typing import Iterator, Optional, Union
import collections
import decimal
import logging
import os

import google.cloud.storage
import pandas

import src.db
import src.settings



GS_BUCKET_NAME = "derisk-persistent-state"



def get_events(
    addresses: tuple[str, ...],
    event_names: tuple[str, ...],
    start_block_number: int = 0,
) -> pandas.DataFrame:
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


class Prices(collections.defaultdict):
    """ A class that describes the prices of tokens. """

    def __init__(self) -> None:
        super().__init__(lambda: None)


class TokenValues(collections.defaultdict):

    def __init__(
        self,
        values: Optional[dict[str, Union[bool, decimal.Decimal]]] = None,
        # TODO: Only one parameter should be specified..
        init_value: decimal.Decimal = decimal.Decimal("0"),
    ) -> None:
        if values:
            super().__init__(decimal.Decimal)
            for token, value in values.items():
                self[token] = value
        else:
            init_function = lambda: init_value
            super().__init__(init_function)


MAX_ROUNDING_ERRORS = collections.defaultdict(
    lambda: decimal.Decimal("5e12"),
    **{
        "ETH": decimal.Decimal("5e12"),
        "wBTC": decimal.Decimal("1e2"),
        "USDC": decimal.Decimal("1e4"),
        "DAI": decimal.Decimal("1e16"),
        "USDT": decimal.Decimal("1e4"),
        "wstETH": decimal.Decimal("5e12"),
        "LORDS": decimal.Decimal("5e12"),
        "STRK": decimal.Decimal("5e12"),
    },
)


class Portfolio(collections.defaultdict):
    """ A class that describes holdings of tokens. """

    MAX_ROUNDING_ERRORS: collections.defaultdict = MAX_ROUNDING_ERRORS

    def __init__(self, token_values: Optional[dict[str, bool | decimal.Decimal]] = None) -> None:
        if token_values is None:
            super().__init__(init_value=decimal.Decimal("0"))
        else:
            super().__init__(values=token_values)

    def __add__(self, second_portfolio: 'Portfolio') -> 'Portfolio':
        if not isinstance(second_portfolio, Portfolio):
            raise TypeError(f"Cannot add Portfolio and {type(second_portfolio)}")
        new_portfolio = self.values.copy()
        for token, amount in second_portfolio.values.items():
            if token in new_portfolio:
                new_portfolio[token] += amount
            else:
                new_portfolio[token] = amount
        return Portfolio(new_portfolio)

    # TODO: Find a better solution to fix the discrepancies.
    def round_small_value_to_zero(self, token: str):
        if abs(self[token]) < self.MAX_ROUNDING_ERRORS[token]:
            self[token] = decimal.Decimal("0")

    def increase_value(self, token: str, value: decimal.Decimal):
        self[token] += value
        self.round_small_value_to_zero(token=token)

    def set_value(self, token: str, value: decimal.Decimal):
        self[token] = value
        self.round_small_value_to_zero(token=token)


def decimal_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal) -> Iterator[decimal.Decimal]:
    while start < stop:
        yield start
        start += step


def get_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal) -> list[decimal.Decimal]:
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
        start = TOKEN_STEP[collateral_token],
        stop = collateral_token_price * decimal.Decimal("1.2"),
        step = TOKEN_STEP[collateral_token],
    )


def load_data(protocol: str) -> tuple[dict[str, pandas.DataFrame], pandas.DataFrame, pandas.DataFrame]:
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in src.settings.PAIRS:
        main_chart_data[pair] = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/{pair}.parquet")
    histogram_data = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/histogram.parquet")
    loans_data = pandas.read_parquet(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/loans.parquet")
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
        for token, token_settings in src.settings.TOKEN_SETTINGS.items()
    }
    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol
    raise KeyError(f"Address = {address} does not exist in the symbol table.")


def upload_file_to_bucket(source_path: str, target_path: str):
    # Initialize the Google Cloud Storage client with the credentials.
    storage_client = google.cloud.storage.Client.from_service_account_json(os.getenv("CREDENTIALS_PATH"))

    # Get the target bucket.
    bucket = storage_client.bucket(GS_BUCKET_NAME)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logging.info(f"File = {source_path} uploaded to = gs://{GS_BUCKET_NAME}/{target_path}")


def save_dataframe(data: pandas.DataFrame, path: str) -> None:
    directory = path.rstrip(path.split('/')[-1])
    if not directory == '':
        os.makedirs(directory, exist_ok=True)
    data.to_parquet(path, index=False, engine = 'fastparquet', compression='gzip')
    src.helpers.upload_file_to_bucket(source_path=path, target_path=path)
    os.remove(path)


def add_leading_zeros(hash: str) -> str:
    '''
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to  
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    '''
    return '0x' + hash[2:].zfill(64)
