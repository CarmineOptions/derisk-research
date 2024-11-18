import asyncio
import logging
import math
from time import monotonic

from data_handler.handlers.loan_states.zklend.events import ZkLendState
from shared.amms import SwapAmm
from shared.constants import TOKEN_SETTINGS

from dashboard_app.data_conector import DataConnector
from dashboard_app.helpers.protocol_stats import (
    get_general_stats,
    get_supply_stats,
    get_collateral_stats,
    get_debt_stats,
    get_utilization_stats
)
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
            state=state, prices=prices
        )

    general_stats = get_general_stats(
        states=states, loan_stats=loan_stats
    )
    supply_stats = get_supply_stats(
        states=states,
        prices=prices,
    )
    collateral_stats = get_collateral_stats(states=states)
    debt_stats = get_debt_stats(states=states)
    utilization_stats = get_utilization_stats(
        general_stats=general_stats,
        supply_stats=supply_stats,
        debt_stats=debt_stats,
    )
    return zklend_state, general_stats, supply_stats, collateral_stats, debt_stats, utilization_stats
