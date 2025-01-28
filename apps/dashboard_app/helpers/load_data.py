"""
This module loads and handle the data.
"""

import asyncio
import logging
import math
from collections import defaultdict
from time import monotonic

from data_handler.handlers.loan_states.zklend.events import ZkLendState
from shared.constants import TOKEN_SETTINGS

from dashboard_app.data_conector import DataConnector
from dashboard_app.helpers.loans_table import get_loans_table_data, get_protocol
from dashboard_app.helpers.protocol_stats import (
    get_collateral_stats,
    get_debt_stats,
    get_general_stats,
    get_supply_stats,
    get_utilization_stats,
)
from dashboard_app.helpers.tools import add_leading_zeros, get_prices

logger = logging.getLogger(__name__)


class DashboardDataHandler:
    """
    Class responsible to handle the data for the dashboard.
    """

    def __init__(self):
        """
        Initialize the data handler.
        """
        self.data_connector = DataConnector()
        self.underlying_addresses_to_decimals = defaultdict(dict)
        self.zklend_state = self._init_zklend_state()
        self.prices = None
        # TODO add also nostra states
        self.states = [
            self.zklend_state,
            # nostra_alpha_state,
            # nostra_mainnet_state,
        ]

    def _init_zklend_state(self) -> ZkLendState:
        """
        Initialize ZkLend state.
        Fetch data from the database and initialize the state.
        :return: Initialized ZkLend state.
        """
        logger.info("Initializing ZkLend state.")
        zklend_state = ZkLendState()
        start = monotonic()
        zklend_data = self.data_connector.fetch_data(
            self.data_connector.ZKLEND_SQL_QUERY
        )
        zklend_interest_rate_data = self.data_connector.fetch_data(
            self.data_connector.ZKLEND_INTEREST_RATE_SQL_QUERY
        )

        zklend_data_dict = zklend_data.to_dict(orient="records")
        for loan_state in zklend_data_dict:
            user_loan_state = zklend_state.loan_entities[loan_state["user"]]
            user_loan_state.collateral_enabled.values = loan_state["collateral_enabled"]
            user_loan_state.collateral.values = loan_state["collateral"]
            user_loan_state.debt.values = loan_state["debt"]

        zklend_state.last_block_number = zklend_data["block"].max()
        zklend_state.interest_rate_models.collateral = zklend_interest_rate_data[
            "collateral"
        ].iloc[0]
        zklend_state.interest_rate_models.debt = zklend_interest_rate_data["debt"].iloc[
            0
        ]
        logger.info("Initialized ZkLend state in %.2fs", monotonic() - start)

        return zklend_state

    def _set_prices(self) -> None:
        """
        Set the prices of the underlying tokens.
        """
        logger.info("Setting prices.")
        self.prices = get_prices(token_decimals=self.underlying_addresses_to_decimals)
        logger.info("Prices set.")

    def _collect_token_parameters(self):
        """
        Collect token parameters.
        :return:
        """
        logger.info("Collecting token parameters.")
        asyncio.run(self.zklend_state.collect_token_parameters())
        logger.info("Token parameters collected.")

    def _set_underlying_addresses_to_decimals(self):
        """
        Set the underlying addresses to decimals.
        """
        logger.info("Setting underlying addresses to decimals.")
        for state in self.states:
            self.underlying_addresses_to_decimals.update(
                {
                    x.underlying_address: x.decimals
                    for x in state.token_parameters.collateral.values()
                }
            )
            self.underlying_addresses_to_decimals.update(
                {
                    x.underlying_address: x.decimals
                    for x in state.token_parameters.debt.values()
                }
            )
        self.underlying_addresses_to_decimals.update(
            {
                add_leading_zeros(x.address): int(math.log10(x.decimal_factor))
                for x in TOKEN_SETTINGS.values()
            }
        )
        logger.info("Underlying addresses to decimals set.")

    def _get_collateral_stats(self) -> dict:
        """
        Get the collateral stats.
        :return: dict
        """
        logger.info("Getting collateral stats.")
        collateral_stats = get_collateral_stats(states=self.states)
        logger.info("Collateral stats collected.")
        return collateral_stats

    def _get_supply_stats(self) -> dict:
        """
        Get the supply stats.
        :return: dict
        """
        logger.info("Getting supply stats.")
        supply_stats = get_supply_stats(
            states=self.states,
            prices=self.prices,
        )
        logger.info("Supply stats collected.")
        return supply_stats

    def _get_general_stats(self, loan_stats) -> dict:
        """
        Get the general stats.
        :return: dict
        """
        logger.info("Getting general stats.")
        general_stats = get_general_stats(states=self.states, loan_stats=loan_stats)
        logger.info("General stats collected.")
        return general_stats

    @staticmethod
    def _get_utilization_stats(
        general_stats: dict, supply_stats: dict, debt_stats: dict
    ) -> dict:
        """
        Get the utilization stats.
        :param general_stats: general_stats dict
        :param supply_stats: supply_stats dict
        :param debt_stats: debt_stats dict
        :return: dict
        """
        logger.info("Getting utilization stats.")
        utilization_stats = get_utilization_stats(
            general_stats=general_stats,
            supply_stats=supply_stats,
            debt_stats=debt_stats,
        )
        logger.info("Utilization stats collected.")
        return utilization_stats

    def _get_debt_stats(self) -> dict:
        """
        Get the debt stats.
        :return: dict
        """
        logger.info("Getting debt stats.")
        debt_stats = get_debt_stats(states=self.states)
        logger.info("Debt stats collected.")
        return debt_stats

    def _get_loan_stats(self) -> dict:
        """
        Get the loan stats.
        :return: dict
        """
        logger.info("Getting loan stats.")
        loan_stats = {}
        for state in self.states:
            protocol = get_protocol(state=state)
            loan_stats[protocol] = get_loans_table_data(state=state, prices=self.prices)
        logger.info("Loan stats collected.")
        return loan_stats

    def load_data(self) -> tuple:
        """
        Get the dashboard data.
        :return: tuple - The dashboard data.
        """
        logger.info("Getting dashboard data.")
        # Get token parameters.
        self._collect_token_parameters()
        # Set the underlying addresses to decimals.
        self._set_underlying_addresses_to_decimals()
        # Set the prices.
        self._set_prices()

        # Get the loan stats.
        loan_stats = self._get_loan_stats()

        # Get the general stats.
        general_stats = self._get_general_stats(loan_stats=loan_stats)
        # Get the supply stats.
        supply_stats = self._get_supply_stats()
        # Get the collateral stats.
        collateral_stats = self._get_collateral_stats()
        # Get the debt stats.
        debt_stats = self._get_debt_stats()
        # Get the utilization stats.
        utilization_stats = self._get_utilization_stats(
            general_stats=general_stats,
            supply_stats=supply_stats,
            debt_stats=debt_stats,
        )
        return (
            self.zklend_state,
            general_stats,
            supply_stats,
            collateral_stats,
            debt_stats,
            utilization_stats,
        )
