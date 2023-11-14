from typing import Iterator, Dict, List, Tuple
import decimal

import pandas

import src.constants
import src.db
import src.hashstack
import src.nostra
import src.nostra_uncapped
import src.zklend



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


def get_directory(state: src.state.State) -> str:
    # TODO: Improve the inference.
    # TODO: rename data -> zklend_data
    if isinstance(state, src.zklend.ZkLendState):
        return "zklend_data"
    if isinstance(state, src.hashstack.HashstackState):
        return "hashstack_data"
    if isinstance(state, src.nostra.NostraState) and not isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "nostra_data"
    if isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "nostra_uncapped_data"
    raise ValueError


def get_protocol(state: src.state.State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, src.zklend.ZkLendState):
        return "zkLend"
    if isinstance(state, src.hashstack.HashstackState):
        return "Hashstack"
    if isinstance(state, src.nostra.NostraState) and not isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "Nostra"
    if isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "Nostra uncapped"
    raise ValueError


def get_supply_function_call_parameters(protocol: str, token: str) -> Tuple[str, str]:
    if protocol == 'zkLend':
        return src.zklend.SUPPLY_ADRESSES[token], 'felt_total_supply'
    if protocol in {'Nostra', 'Nostra uncapped'}:
        return src.nostra.SUPPLY_ADRESSES[token], 'totalSupply'
    raise ValueError


def get_hashstack_supply_parameters(token: str) -> Tuple[str, str]:
    return src.hashstack.SUPPLY_TOKEN_ADRESSES[token], src.hashstack.SUPPLY_HOLDER_ADRESSES[token]


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