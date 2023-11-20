from typing import Iterator, Dict, List, Optional, Tuple
import decimal

import pandas

import src.constants
import src.db



def get_events(
    adresses: Tuple[str, ...],
    events: Tuple[str, ...],
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
    def __init__(self, values: Optional[Dict[str, decimal.Decimal]] = None, init_value: decimal.Decimal = decimal.Decimal("0")) -> None:
        if values:
            assert set(values.keys()) == set(src.constants.TOKEN_SETTINGS.keys())
            self.values = values
        else:
            self.values: Dict[str, decimal.Decimal] = {
                token: init_value
                for token in src.constants.TOKEN_SETTINGS
            }


class Portfolio(TokenValues):
    """ A class that describes holdings of tokens. """

    # TODO: Find a better solution to fix the discrepancies.
    # TODO: Use TokenValues?
    MAX_ROUNDING_ERRORS: Dict[str, decimal.Decimal] = {
        "ETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
        "wBTC": decimal.Decimal("1e2"),
        "USDC": decimal.Decimal("1e4"),
        "DAI": decimal.Decimal("1e16"),
        "USDT": decimal.Decimal("1e4"),
        "wstETH": decimal.Decimal("0.5") * decimal.Decimal("1e13"),
    }

    def __init__(self) -> None:
        super().__init__(init_value=decimal.Decimal("0"))

    def round_small_value_to_zero(self, token: str):
        if (
            -self.MAX_ROUNDING_ERRORS[token]
            < self.values[token]
            < self.MAX_ROUNDING_ERRORS[token]
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


def get_range(start: decimal.Decimal, stop: decimal.Decimal, step: decimal.Decimal) -> List[decimal.Decimal]:
    return [x for x in decimal_range(start=start, stop=stop, step=step)]


def get_collateral_token_range(collateral_token: str) -> List[decimal.Decimal]:
    assert collateral_token in {"ETH", "wBTC"}
    if collateral_token == "ETH":
        return get_range(decimal.Decimal("50"), decimal.Decimal("2500"), decimal.Decimal("50"))
    return get_range(decimal.Decimal("250"), decimal.Decimal("40000"), decimal.Decimal("250"))


def load_data(protocol: str) -> Tuple[Dict[str, pandas.DataFrame], pandas.DataFrame, pandas.DataFrame]:
    directory = f"{protocol.lower().replace(' ', '_')}_data"
    main_chart_data = {}
    for pair in src.constants.PAIRS:
        main_chart_data[pair] = pandas.read_csv(f"{directory}/{pair}.csv", compression="gzip")
    histogram_data = pandas.read_csv(f"{directory}/histogram.csv", compression="gzip")
    loans_data = pandas.read_csv(f"{directory}/loans.csv", compression="gzip")
    return (
        main_chart_data,
        histogram_data,
        loans_data,
    )