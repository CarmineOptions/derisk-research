from typing import Iterator, Optional, Union
import decimal
import logging
import os

import google.cloud.storage
import pandas

import src.db
import src.settings



GS_BUCKET_NAME = "derisk-persistent-state"



def get_events(
    adresses: tuple[str, ...],
    events: tuple[str, ...],
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
                from_address IN {adresses}
            AND
                key_name IN {events}
            AND
                block_number >= {start_block_number}
            ORDER BY
                block_number, id ASC;
        """,
        con=connection,
    )
    connection.close()
    return events.set_index("id")


class TokenValues:
    def __init__(self, values: Optional[dict[str, Union[bool, decimal.Decimal]]] = None, init_value: decimal.Decimal = decimal.Decimal("0")) -> None:
        if values:
            assert set(values.keys()) == set(src.settings.TOKEN_SETTINGS.keys())
            self.values: dict[str, decimal.Decimal] = values
        else:
            self.values: dict[str, decimal.Decimal] = {
                token: init_value
                for token in src.settings.TOKEN_SETTINGS
            }


class Portfolio(TokenValues):
    """ A class that describes holdings of tokens. """

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
        },
    )

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


def decimal_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal) -> Iterator[decimal.Decimal]:
    while start < stop:
        yield start
        start += step


def get_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal) -> list[decimal.Decimal]:
    return [x for x in decimal_range(start=start, stop=stop, step=step)]


def get_collateral_token_range(collateral_token: str) -> list[decimal.Decimal]:
    assert collateral_token in {"ETH", "wBTC"}
    if collateral_token == "ETH":
        return get_range(decimal.Decimal("50"), decimal.Decimal("2500"), decimal.Decimal("50"))
    return get_range(decimal.Decimal("250"), decimal.Decimal("40000"), decimal.Decimal("250"))


def load_data(protocol: str) -> tuple[dict[str, pandas.DataFrame], pandas.DataFrame, pandas.DataFrame]:
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in src.settings.PAIRS:
        main_chart_data[pair] = pandas.read_csv(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/{pair}.csv", compression="gzip")
    histogram_data = pandas.read_csv(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/histogram.csv", compression="gzip")
    loans_data = pandas.read_csv(f"gs://{src.helpers.GS_BUCKET_NAME}/{directory}/loans.csv", compression="gzip")
    return (
        main_chart_data,
        histogram_data,
        loans_data,
    )


# TODO: Improve this.
def get_symbol(address: str) -> str:
    # you can match addresses as numbers
    n = int(address, base=16)
    symbol_address_map = {token: token_settings.address for token, token_settings in src.settings.TOKEN_SETTINGS.items()}
    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol
    raise KeyError(f"Address = {address} does not exist in the symbol table.")


def ztoken_to_token(symbol: str) -> str:
    if symbol == "zWBTC":
        # weird exception
        return "wBTC"
    if symbol.startswith("z"):
        return symbol[1:]
    else:
        return symbol


def upload_file_to_bucket(source_path: str, target_path: str):
    # Initialize the Google Cloud Storage client with the credentials.
    storage_client = google.cloud.storage.Client.from_service_account_json(os.getenv("CREDENTIALS_PATH"))

    # Get the target bucket.
    bucket = storage_client.bucket(GS_BUCKET_NAME)

    # Upload the file to the bucket.
    blob = bucket.blob(target_path)
    blob.upload_from_filename(source_path)
    logging.info(f"File = {source_path} uploaded to = gs://{GS_BUCKET_NAME}/{target_path}")