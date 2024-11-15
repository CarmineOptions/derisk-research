import asyncio
import itertools
import logging
import math
import time

import pandas



import src.loans_table
import src.main_chart
import src.persistent_state
import src.protocol_stats
import src.protocol_parameters
import src.settings
import src.swap_amm
import src.zklend

from data_conector import DataConnector
from shared.constants import ZKLEND
from shared.protocol_states.zklend import ZkLendState
from shared.protocol_initializers.zklend import ZkLendInitializer
from helpers.tools import get_prices, GS_BUCKET_NAME

def update_data(zklend_state: src.zklend.ZkLendState):
    logging.info(f"Updating SQL data from {zklend_state.last_block_number}...")
    time_end = time.time()
    # TODO: parallelize per protocol
    # TODO: stream the data, don't wait until we get all events
    zklend_events = src.zklend.zklend_get_events(
        start_block_number=zklend_state.last_block_number + 1
    )

    logging.info(
        f"got = {len(zklend_events)} events in {time.time() - time_end}s"
    )  # TODO: this log will become obsolete

    # Iterate over ordered events to obtain the final state of each user.
    t1 = time.time()
    for _, zklend_event in zklend_events.iterrows():
        zklend_state.process_event(event=zklend_event)

    logging.info(f"updated state in {time.time() - t1}s")

    # TODO: move this to state inits above?
    # # Collect token parameters.
    t2 = time.time()
    asyncio.run(zklend_state.collect_token_parameters())
    logging.info(f"collected token parameters in {time.time() - t2}s")

    # Get prices of the underlying tokens.
    t_prices = time.time()
    states = [
        zklend_state,
    ]
    underlying_addresses_to_decimals = {}
    for state in states:
        underlying_addresses_to_decimals.update(
            {
                x.underlying_address: x.decimals
                for x in state.token_parameters.collateral.values()
            }
        )
        underlying_addresses_to_decimals.update(
            {
                x.underlying_address: x.decimals
                for x in state.token_parameters.debt.values()
            }
        )
    underlying_addresses_to_decimals.update(
        {
            x.address: int(math.log10(x.decimal_factor))
            for x in src.settings.TOKEN_SETTINGS.values()
        }
    )
    prices = get_prices(token_decimals=underlying_addresses_to_decimals)
    logging.info(f"prices in {time.time() - t_prices}s")

    t_swap = time.time()
    swap_amms = src.swap_amm.SwapAmm()
    asyncio.run(swap_amms.init())
    logging.info(f"swap in {time.time() - t_swap}s")

    t3 = time.time()
    for pair, state in itertools.product(src.settings.PAIRS, states):
        protocol = src.protocol_parameters.get_protocol(state=state)
        logging.info(
            f"Preparing main chart data for protocol = {protocol} and pair = {pair}."
        )
        # TODO: Decipher `pair` in a smarter way.
        collateral_token_underlying_symbol, debt_token_underlying_symbol = pair.split(
            "-"
        )
        _ = src.main_chart.get_main_chart_data(
            state=state,
            prices=prices,
            swap_amms=swap_amms,
            collateral_token_underlying_symbol=collateral_token_underlying_symbol,
            debt_token_underlying_symbol=debt_token_underlying_symbol,
            save_data=True,
        )
        logging.info(
            f"Main chart data for protocol = {protocol} and pair = {pair} prepared in {time.time() - t3}s"
        )
    logging.info(f"updated graphs in {time.time() - t3}s")

    loan_stats = {}
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        loan_stats[protocol] = src.loans_table.get_loans_table_data(
            state=state, prices=prices, save_data=True
        )

    general_stats = src.protocol_stats.get_general_stats(
        states=states, loan_stats=loan_stats, save_data=True
    )
    supply_stats = src.protocol_stats.get_supply_stats(
        states=states,
        prices=prices,
        save_data=True,
    )
    _ = src.protocol_stats.get_collateral_stats(states=states, save_data=True)
    debt_stats = src.protocol_stats.get_debt_stats(states=states, save_data=True)
    _ = src.protocol_stats.get_utilization_stats(
        general_stats=general_stats,
        supply_stats=supply_stats,
        debt_stats=debt_stats,
        save_data=True,
    )

    max_block_number = zklend_events["block_number"].max()
    max_timestamp = zklend_events["timestamp"].max()
    last_update = {
        "timestamp": str(max_timestamp),
        "block_number": str(max_block_number),
    }
    src.persistent_state.upload_object_as_pickle(
        last_update, path=src.persistent_state.LAST_UPDATE_FILENAME
    )
    zklend_state.save_loan_entities(
        path=src.persistent_state.PERSISTENT_STATE_LOAN_ENTITIES_FILENAME
    )
    zklend_state.clear_loan_entities()
    src.persistent_state.upload_object_as_pickle(
        zklend_state, path=src.persistent_state.PERSISTENT_STATE_FILENAME
    )
    loan_entities = pandas.read_parquet(
        f"gs://{GS_BUCKET_NAME}/{src.persistent_state.PERSISTENT_STATE_LOAN_ENTITIES_FILENAME}",
        engine="fastparquet",
    )
    zklend_state.set_loan_entities(loan_entities=loan_entities)
    logging.info(f"Updated CSV data in {time.time() - time_end}s")

    return zklend_state


if __name__ == "__name__":
    # Fetching data from DB
    connector = DataConnector()
    loan_states_data_frame = connector.fetch_data("loan_state", ZKLEND)

    # Initializing ZkLend state
    zklend_state = ZkLendState()
    zklend_initializer = ZkLendInitializer(zklend_state)
    user_ids = zklend_initializer.get_user_ids_from_df(loan_states_data_frame)
    zklend_initializer.set_last_loan_states_per_users(user_ids)

    # Updating data
    zklend_initializer.zklend_state = update_data(zklend_initializer.zklend_state)
    print(zklend_initializer.zklend_state)
