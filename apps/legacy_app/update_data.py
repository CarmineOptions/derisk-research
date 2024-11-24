import asyncio
import itertools
import logging
import math
import time

import pandas

import src.hashstack_v0
import src.hashstack_v1
import src.helpers
import src.loans_table
import src.main_chart
import src.nostra_alpha
import src.nostra_mainnet
import src.persistent_state
import src.protocol_parameters
import src.protocol_stats
import src.settings
import src.swap_amm
import src.zklend


def update_data(zklend_state: src.zklend.ZkLendState):
    logging.info(f"Updating CSV data from {zklend_state.last_block_number}...")
    t0 = time.time()
    # TODO: parallelize per protocol
    # TODO: stream the data, don't wait until we get all events
    zklend_events = src.zklend.zklend_get_events(
        start_block_number=zklend_state.last_block_number + 1
    )
    # hashstack_v0_events = src.hashstack_v0.hashstack_v0_get_events()
    # hashstack_v1_events = src.hashstack_v1.hashstack_v1_get_events()
    nostra_alpha_events = src.nostra_alpha.nostra_alpha_get_events()
    nostra_mainnet_events = src.nostra_mainnet.nostra_mainnet_get_events()
    logging.info(
        f"got = {len(zklend_events)} events in {time.time() - t0}s"
    )  # TODO: this log will become obsolete

    # Iterate over ordered events to obtain the final state of each user.
    t1 = time.time()
    for _, zklend_event in zklend_events.iterrows():
        zklend_state.process_event(event=zklend_event)

    # hashstack_v0_state = src.hashstack_v0.HashstackV0State()
    # for _, hashstack_v0_event in hashstack_v0_events.iterrows():
    #     hashstack_v0_state.process_event(event=hashstack_v0_event)

    # hashstack_v1_state = src.hashstack_v1.HashstackV1State()
    # for _, hashstack_v1_event in hashstack_v1_events.iterrows():
    #     # TODO: Do not crash if there is an unrecognized Hashstack V1 event.
    #     try:
    #         hashstack_v1_state.process_event(event=hashstack_v1_event)
    #     except:
    #         logging.error("Failed to process Hashstack event = {}.".format(hashstack_v1_event))
    #         continue

    nostra_alpha_state = src.nostra_alpha.NostraAlphaState()
    for _, nostra_alpha_event in nostra_alpha_events.iterrows():
        nostra_alpha_state.process_event(event=nostra_alpha_event)

    nostra_mainnet_state = src.nostra_mainnet.NostraMainnetState()
    for _, nostra_mainnet_event in nostra_mainnet_events.iterrows():
        nostra_mainnet_state.process_event(event=nostra_mainnet_event)
    logging.info(f"updated state in {time.time() - t1}s")

    # TODO: move this to state inits above?
    # # Collect token parameters.
    t2 = time.time()
    asyncio.run(zklend_state.collect_token_parameters())
    # asyncio.run(hashstack_v0_state.collect_token_parameters())
    # asyncio.run(hashstack_v1_state.collect_token_parameters())
    logging.info(f"collected token parameters in {time.time() - t2}s")
    # TODO move it to separated function
    # Get prices of the underlying tokens.
    t_prices = time.time()
    states = [
        zklend_state,
        # hashstack_v0_state,
        # hashstack_v1_state,
        nostra_alpha_state,
        nostra_mainnet_state,
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
    prices = src.helpers.get_prices(token_decimals=underlying_addresses_to_decimals)
    logging.info(f"prices in {time.time() - t_prices}s")
    # TODO: move it to separated function END
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
        f"gs://{src.helpers.GS_BUCKET_NAME}/{src.persistent_state.PERSISTENT_STATE_LOAN_ENTITIES_FILENAME}",
        engine="fastparquet",
    )
    zklend_state.set_loan_entities(loan_entities=loan_entities)
    logging.info(f"Updated CSV data in {time.time() - t0}s")
    return zklend_state


def update_data_continuously():
    state = src.persistent_state.load_pickle(
        path=src.persistent_state.PERSISTENT_STATE_FILENAME
    )
    if state.last_block_number > 0:
        loan_entities = pandas.read_parquet(
            f"gs://{src.helpers.GS_BUCKET_NAME}/{src.persistent_state.PERSISTENT_STATE_LOAN_ENTITIES_FILENAME}",
            engine="fastparquet",
        )
        state.set_loan_entities(loan_entities=loan_entities)
    while True:
        state = update_data(state)
        logging.info("DATA UPDATED")
        time.sleep(120)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    zklend_state = src.persistent_state.load_pickle(
        path=src.persistent_state.PERSISTENT_STATE_FILENAME
    )
    if zklend_state.last_block_number > 0:
        loan_entities = pandas.read_parquet(
            f"gs://{src.helpers.GS_BUCKET_NAME}/{src.persistent_state.PERSISTENT_STATE_LOAN_ENTITIES_FILENAME}",
            engine="fastparquet",
        )
        zklend_state.set_loan_entities(loan_entities=loan_entities)
    update_data(zklend_state)
