import uuid
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Type

from db.crud import DBConnector

from handlers.helpers import TokenValues
from handlers.state import State, LoanEntity
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity
from handlers.loan_states.nostra_alpha.events import NostraAlphaState, NostraAlphaLoanEntity
from handlers.loan_states.nostra_mainnet.events import NostraMainnetState, NostraMainnetLoanEntity
from handler_tools.constants import ProtocolIDs
from handlers.liquidable_debt.utils import Prices
from handlers.liquidable_debt.values import (USER_FIELD_NAME, HEALTH_FACTOR_FIELD_NAME,
                                             TIMESTAMP_FIELD_NAME)


class BaseHealthRatioHandler:
    """
    A base handler class that collects data from DB,
    computes health_ratio level and stores it in the database.
    """

    def __init__(self, state_class: Type[State], loan_entity_class: Type[LoanEntity]):
        self.state_class = state_class
        self.loan_entity_class = loan_entity_class
        self.db_connector = DBConnector()

    def fetch_data(self, protocol_name: ProtocolIDs) -> tuple:
        """
        Prepares the data for the given protocol.
        :param protocol_name: Protocol name.
        :return: tuple
        """
        loan_states_data = self.db_connector.get_latest_block_loans()
        interest_rate_models = self.db_connector.get_last_interest_rate_record_by_protocol_id(protocol_id=protocol_name)

        return loan_states_data, interest_rate_models

    def initialize_loan_entities(self, state: State, data: dict = None) -> State:
        """
        Initializes the loan entities in a state instance.
        :param state: State
        :param data: dict
        :return: State
        """
        for instance in data:
            loan_entity = self.loan_entity_class()

            loan_entity.debt = TokenValues(values=instance.debt)
            loan_entity.collateral = TokenValues(values=instance.collateral)

            state.loan_entities.update(
                {
                    instance.user: loan_entity,
                }
            )

        return state

    @staticmethod
    def health_ratio_is_valid(health_ratio_level: Decimal) -> bool:
        """
        Checks if the given health ratio level is valid.
        :param health_ratio_level: Health ratio level
        :return: bool
        """
        return (health_ratio_level > Decimal("0") and
                health_ratio_level != Decimal("Infinity"))


class ZkLendHealthRatioHandler(BaseHealthRatioHandler):
    """
    A zkLend handler that collects data from DB,
    computes health_ratio level and stores it in the database.

    :cvar CONNECTOR: A DB connection object.
    """

    def __init__(self):
        super().__init__(state_class=ZkLendState, loan_entity_class=ZkLendLoanEntity)

    def calculate_health_ratio(self) -> list[dict]:
        """
        Calculates health ratio based on provided data.
        :return: A list of the ready health ratio data.
        """
        data, interest_rate_models = self.fetch_data(protocol_name=ProtocolIDs.ZKLEND.value)
        state = self.state_class()
        state = self.initialize_loan_entities(state=state, data=data)

        # Set up collateral and debt interest rate models
        state.collateral_interest_rate_models = TokenValues(
            values=interest_rate_models.collateral
        )
        state.debt_interest_rate_models = TokenValues(
            values=interest_rate_models.debt
        )

        current_prices = Prices()
        asyncio.run(current_prices.get_lp_token_prices())

        result_data = list()
        prices = TokenValues(values=current_prices.prices.values)

        for user_id, loan_entity in state.loan_entities.items():
            risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_models=state.collateral_interest_rate_models,
                prices=prices,
            )
            debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=False,
                debt_interest_rate_models=state.debt_interest_rate_models,
                prices=prices,
            )
            health_ratio_level = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                debt_usd=debt_usd,
            )

            if self.health_ratio_is_valid(health_ratio_level):
                result_data.append({
                        USER_FIELD_NAME: user_id,
                        HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                        TIMESTAMP_FIELD_NAME: datetime.now().timestamp()
                    }
                )

        return result_data


class NostrAlphaHealthRatioHandler(BaseHealthRatioHandler):
    """
    A Nostra Alha handler that collects data from DB,
    computes health_ratio level and stores it in the database.
    """

    def __init__(self):
        super().__init__(state_class=NostraAlphaState, loan_entity_class=NostraAlphaLoanEntity)

    def calculate_health_ratio(self) -> list[dict]:
        """
        Calculates health ratio based on provided data.
        :return: A list of the ready health ratio data.
        """
        data, interest_rate_models = self.fetch_data(protocol_name=ProtocolIDs.NOSTRA_ALPHA.value)
        state = self.state_class()
        state = self.initialize_loan_entities(state=state, data=data)

        # Set up collateral and debt interest rate models
        state.collateral_interest_rate_models = TokenValues(
            values=interest_rate_models.collateral
        )
        state.debt_interest_rate_models = TokenValues(
            values=interest_rate_models.debt
        )

        current_prices = Prices()
        asyncio.run(current_prices.get_lp_token_prices())

        result_data = list()
        prices = TokenValues(values=current_prices.prices.values)

        for user_id, loan_entity in state.loan_entities.items():
            risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_models=state.collateral_interest_rate_models,
                prices=prices,
            )
            risk_adjusted_debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=True,
                debt_interest_rate_models=state.debt_interest_rate_models,
                prices=prices,
            )
            health_ratio_level = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd
            )

            if self.health_ratio_is_valid(health_ratio_level):
                result_data.append({
                        USER_FIELD_NAME: user_id,
                        HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                        TIMESTAMP_FIELD_NAME: datetime.now().timestamp()
                    }
                )

        return result_data


class NostrMainnetHealthRatioHandler(BaseHealthRatioHandler):
    """
    A Nostra Mainnet handler that collects data from DB,
    computes health_ratio level and stores it in the database.
    """

    def __init__(self):
        super().__init__(state_class=NostraMainnetState, loan_entity_class=NostraMainnetLoanEntity)

    def calculate_health_ratio(self) -> list[dict]:
        """
        Calculates health ratio based on provided data.
        :return: A list of the ready health ratio data.
        """
        data, interest_rate_models = self.fetch_data(protocol_name=ProtocolIDs.NOSTRA_MAINNET.value)
        state = self.state_class()
        state = self.initialize_loan_entities(state=state, data=data)

        # Set up collateral and debt interest rate models
        state.collateral_interest_rate_models = TokenValues(
            values=interest_rate_models.collateral
        )
        state.debt_interest_rate_models = TokenValues(
            values=interest_rate_models.debt
        )

        current_prices = Prices()
        asyncio.run(current_prices.get_lp_token_prices())

        result_data = list()
        prices = TokenValues(values=current_prices.prices.values)

        for user_id, loan_entity in state.loan_entities.items():
            risk_adjusted_collateral_usd = loan_entity.compute_collateral_usd(
                risk_adjusted=True,
                collateral_interest_rate_models=state.collateral_interest_rate_models,
                prices=prices,
            )
            risk_adjusted_debt_usd = loan_entity.compute_debt_usd(
                risk_adjusted=True,
                debt_interest_rate_models=state.debt_interest_rate_models,
                prices=prices,
            )
            health_ratio_level = loan_entity.compute_health_factor(
                standardized=False,
                risk_adjusted_collateral_usd=risk_adjusted_collateral_usd,
                risk_adjusted_debt_usd=risk_adjusted_debt_usd
            )

            if self.health_ratio_is_valid(health_ratio_level):
                result_data.append({
                        USER_FIELD_NAME: user_id,
                        HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                        TIMESTAMP_FIELD_NAME: datetime.now().timestamp()
                    }
                )

        return result_data
