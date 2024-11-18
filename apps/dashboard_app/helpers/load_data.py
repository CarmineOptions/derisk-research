import asyncio
import itertools
import logging
import math
from time import monotonic

from data_handler.handlers.loan_states.zklend.events import ZkLendState
from shared.amms import SwapAmm
from shared.constants import TOKEN_SETTINGS

from dashboard_app.data_conector import DataConnector
from dashboard_app.helpers.loans_table import get_loans_table_data, get_protocol
from dashboard_app.helpers.tools import get_prices

loger = logging.getLogger(__name__)
data_connector = DataConnector()


def init_zklend_state():
    zklend_state = ZkLendState()
    start = monotonic()
    zklend_data = data_connector.fetch_data(data_connector.ZKLEND_SQL_QUERY)
    zklend_data_dict = zklend_data.to_dict(orient="records")
    for loan_state in zklend_data_dict:
        user_loan_state = zklend_state.loan_entities[loan_state["user"]]
        user_loan_state.collateral_enabled.values = loan_state["collateral_enabled"]
        user_loan_state.collateral.values = loan_state["collateral"]
        user_loan_state.debt.values = loan_state["debt"]

    zklend_state.last_block_number = zklend_data["block"].max()
    print(f"Initialized ZkLend state in {monotonic() - start:.2f}s")


if __name__ == "__main__":
    init_zklend_state()
    # TODO: Implement periodic updates


def update_data(zklend_state: ZkLendState):
    # TODO: parallelize per protocol
    # TODO: stream the data, don't wait until we get all events
    # nostra_alpha_events = src.nostra_alpha.nostra_alpha_get_events()
    # nostra_mainnet_events = src.nostra_mainnet.nostra_mainnet_get_events()

    # Iterate over ordered events to obtain the final state of each user.

    # nostra_alpha_state = src.nostra_alpha.NostraAlphaState()
    # for _, nostra_alpha_event in nostra_alpha_events.iterrows():
    #     nostra_alpha_state.process_event(event=nostra_alpha_event)
    #
    # nostra_mainnet_state = src.nostra_mainnet.NostraMainnetState()
    # for _, nostra_mainnet_event in nostra_mainnet_events.iterrows():
    #     nostra_mainnet_state.process_event(event=nostra_mainnet_event)
    # logging.info(f"updated state in {time.time() - t1}s")

    # TODO: move this to state inits above?
    # # Collect token parameters.
    asyncio.run(zklend_state.collect_token_parameters())
    # TODO move it to separated function
    # Get prices of the underlying tokens.
    states = [
        zklend_state,
        # nostra_alpha_state,
        # nostra_mainnet_state,
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
        {x.address: int(math.log10(x.decimal_factor)) for x in TOKEN_SETTINGS.values()}
    )
    prices = get_prices(token_decimals=underlying_addresses_to_decimals)
    # TODO: move it to separated function END
    swap_amms = SwapAmm()
    asyncio.run(swap_amms.init())

    # for pair, state in itertools.product(PAIRS, states):
    #     protocol = src.protocol_parameters.get_protocol(state=state)
    #     logging.info(
    #         f"Preparing main chart data for protocol = {protocol} and pair = {pair}."
    #     )
    #     # TODO: Decipher `pair` in a smarter way.
    #     collateral_token_underlying_symbol, debt_token_underlying_symbol = pair.split(
    #         "-"
    #     )
    #     _ = src.main_chart.get_main_chart_data(
    #         state=state,
    #         prices=prices,
    #         swap_amms=swap_amms,
    #         collateral_token_underlying_symbol=collateral_token_underlying_symbol,
    #         debt_token_underlying_symbol=debt_token_underlying_symbol,
    #         save_data=True,
    #     )
    #     logging.info(
    #         f"Main chart data for protocol = {protocol} and pair = {pair} prepared in {time.time() - t3}s"
    #     )

    loan_stats = {}
    for state in states:
        protocol = get_protocol(state=state)
        loan_stats[protocol] = get_loans_table_data(
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
