import asyncio
import itertools
import logging
import time

import src.settings
import src.hashstack_v0
import src.hashstack_v1
import src.histogram
import src.loans_table
import src.main_chart
import src.nostra_alpha
import src.nostra_mainnet
import src.persistent_state
import src.protocol_parameters
import src.protocol_stats
import src.swap_amm
import src.zklend



logging.basicConfig(level=logging.INFO)



def update_data(zklend_state):
    t0 = time.time()
    logging.info(f"Updating CSV data from {zklend_state.last_block_number}...")
    zklend_events = src.zklend.get_events(start_block_number = zklend_state.last_block_number + 1)
    hashstack_v0_events = src.hashstack_v0.get_events()
    hashstack_v1_events = src.hashstack_v1.get_events()
    nostra_alpha_events = src.nostra_alpha.get_events()
    nostra_mainnet_events = src.nostra_mainnet.get_events()
    logging.info(f"got events in {time.time() - t0}s")

    t1 = time.time()

    # Iterate over ordered events to obtain the final state of each user.
    for _, zklend_event in zklend_events.iterrows():
        zklend_state.process_event(event=zklend_event)

    hashstack_v0_state = src.hashstack_v0.HashstackV0State()
    for _, hashstack_v0_event in hashstack_v0_events.iterrows():
        hashstack_v0_state.process_event(event=hashstack_v0_event)

    hashstack_v1_state = src.hashstack_v1.HashstackV1State()
    for _, hashstack_v1_event in hashstack_v1_events.iterrows():
        # TODO: Do not crash if there is an unrecognized Hashstack V1 event.
        try:
            hashstack_v1_state.process_event(event=hashstack_v1_event)
        except:
            logging.error("Failed to process Hashstack event = {}.".format(hashstack_v1_event))
            continue

    nostra_alpha_state = src.nostra_alpha.NostraAlphaState()
    for _, nostra_alpha_event in nostra_alpha_events.iterrows():
        nostra_alpha_state.process_event(event=nostra_alpha_event)

    nostra_mainnet_state = src.nostra_mainnet.NostraMainnetState()
    for _, nostra_mainnet_event in nostra_mainnet_events.iterrows():
        nostra_mainnet_state.process_event(event=nostra_mainnet_event)

    logging.info(f"updated state in {time.time() - t1}s")

    t_prices = time.time()
    prices = src.swap_amm.Prices()
    asyncio.run(prices.get_lp_token_prices())

    logging.info(f"prices in {time.time() - t_prices}s")

    t_swap = time.time()

    swap_amms = src.swap_amm.SwapAmm()
    asyncio.run(swap_amms.init())

    logging.info(f"swap in {time.time() - t_swap}s")

    t2 = time.time()

    states = [
        zklend_state,
        hashstack_v0_state, 
        hashstack_v1_state, 
        nostra_alpha_state, 
        nostra_mainnet_state,
    ]
    for pair, state in itertools.product(src.settings.PAIRS, states):
        # TODO: Decipher `pair` in a smarter way.
        collateral_token, borrowings_token = pair.split("-")
        _ = src.main_chart.get_main_chart_data(
            state=state,
            prices=prices.prices,
            swap_amms=swap_amms,
            collateral_token=collateral_token,
            debt_token=borrowings_token,
            save_data=False,
        )
        logging.info(f"Main chart data for pair = {pair} prepared in {time.time() - t2}s")

    logging.info(f"updated graphs in {time.time() - t2}s")

    for state in states:
        _ = src.histogram.get_histogram_data(state=state, prices=prices.prices, save_data=False)

    loan_stats = {}
    for state in states:
        protocol = src.protocol_parameters.get_protocol(state=state)
        loan_stats[protocol] = src.loans_table.get_loans_table_data(state=state, prices=prices.prices, save_data=False)

    # general_stats = src.protocol_stats.get_general_stats(states=states, loan_stats=loan_stats, save_data=True)
    # supply_stats = src.protocol_stats.get_supply_stats(states=states, prices=prices.prices, save_data=True)
    # _ = src.protocol_stats.get_collateral_stats(states=states, save_data=False)
    # debt_stats = src.protocol_stats.get_debt_stats(states=states, save_data=False)
    # _ = src.protocol_stats.get_utilization_stats(
        # general_stats=general_stats,
        # supply_stats=supply_stats, 
        # debt_stats=debt_stats, 
        # save_data=False,
    # )

    # max_block_number = zklend_events["block_number"].max()
    # max_timestamp = zklend_events["timestamp"].max()
    # last_update = {"timestamp": str(max_timestamp), "block_number": str(max_block_number)}
    # src.persistent_state.upload_object_as_pickle(last_update, path=src.persistent_state.LAST_UPDATE_FILENAME)

    logging.info(f"Updated CSV data in {time.time() - t0}s")
    return zklend_state


def update_data_continuously():
    state = src.persistent_state.load_pickle(path=src.persistent_state.PERSISTENT_STATE_FILENAME)
    while True:
        state = update_data(state)
        # src.persistent_state.upload_object_as_pickle(state, path=src.persistent_state.PERSISTENT_STATE_FILENAME)
        logging.info("DATA UPDATED")
        time.sleep(120)


if __name__ == "__main__":
    update_data(src.zklend.ZkLendState())
