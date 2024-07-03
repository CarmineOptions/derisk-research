import uuid
import asyncio
from datetime import datetime
from decimal import Decimal
from collections import defaultdict

from db.crud import DBConnector
from db.models import HealthRatioLevel, LoanState

from handlers.helpers import TokenValues
from handlers.state import State, LoanEntity
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity
from handlers.loan_states.nostra_alpha.events import NostraAlphaState, NostraAlphaLoanEntity
from handlers.loan_states.nostra_mainnet.events import NostraMainnetState, NostraMainnetLoanEntity
from handler_tools.constants import ProtocolIDs
from handlers.liquidable_debt.utils import Prices
from handlers.liquidable_debt.values import (USER_FIELD_NAME, HEALTH_FACTOR_FIELD_NAME,
                                             TIMESTAMP_FIELD_NAME, PROTOCOL_FIELD_NAME)


class BaseHealthRatioHandler:
    """
    A base handler class that collects data from DB,
    computes health_ratio level and stores it in the database.

    :cvar CONNECTOR: A DB connection object.
    """
    CONNECTOR = DBConnector()

    def __init__(self, state_class: State = None, loan_entity_class: LoanEntity = None):
        self.state_class = state_class
        self.loan_entity_class = loan_entity_class

    def fetch_data(self, protocol_name: str) -> tuple:
        """
        Prepares the data for the given protocol.
        :param protocol_name: Protocol name.
        :return: tuple
        """
        fetched_data = self.get_data_from_db()
        interest_rate_models = self.get_interest_rate_models_from_db(
            protocol_id=protocol_name
        )

        return fetched_data, interest_rate_models

    @classmethod
    def get_interest_rate_models_from_db(cls, protocol_id: str) -> dict:
        """
        Returns interest rate models data from DB.
        :param protocol_id: str
        :return: dict
        """
        return cls.CONNECTOR.get_last_interest_rate_record_by_protocol_id(protocol_id=protocol_id)

    @classmethod
    def get_data_from_db(cls) -> dict:
        """
        Gets the data from the database based on the protocol name.
        :return: The data from the database.
        """
        return cls.CONNECTOR.get_latest_block_loans()

    @classmethod
    def write_to_db(cls, data: HealthRatioLevel = None) -> None:
        """
        Writes the data into the database.
        :param data: A dictionary of the parsed data.
        :return: None
        """
        cls.CONNECTOR.write_to_db(data)

    @staticmethod
    def health_ratio_is_valid(health_ratio_level: Decimal = None) -> bool:
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

    def calculate_health_ratio(self) -> defaultdict:
        """
        Calculates health ratio based on provided data.
        :return: A dictionary of the ready health ratio data.
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

        result_data = defaultdict()
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
                result_data.update({
                    f"{uuid.uuid4()}": {
                        USER_FIELD_NAME: user_id,
                        HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                        TIMESTAMP_FIELD_NAME: datetime.now().timestamp(),
                        PROTOCOL_FIELD_NAME: ProtocolIDs.ZKLEND.value
                    }
                })

        return result_data


class NostrAlphaHealthRatioHandler(BaseHealthRatioHandler):
    """
    A Nostra Alha handler that collects data from DB,
    computes health_ratio level and stores it in the database.

    :cvar CONNECTOR: A DB connection object.
    """
    def __init__(self):
        super().__init__(state_class=NostraAlphaState, loan_entity_class=NostraAlphaLoanEntity)

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

    def calculate_health_ratio(self) -> defaultdict:
        """
        Calculates health ratio based on provided data.
        :return: A dictionary of the ready health ratio data.
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

        result_data = defaultdict()
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
                result_data.update({
                    f"{uuid.uuid4()}": {
                        USER_FIELD_NAME: user_id,
                        HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                        TIMESTAMP_FIELD_NAME: datetime.now().timestamp(),
                        PROTOCOL_FIELD_NAME: ProtocolIDs.NOSTRA_ALPHA.value
                    }
                })

        return result_data


class NostrMainnetHealthRatioHandler(BaseHealthRatioHandler):
    """
    A Nostra Mainnet handler that collects data from DB,
    computes health_ratio level and stores it in the database.

    :cvar CONNECTOR: A DB connection object.
    """
    def __init__(self):
        super().__init__(state_class=NostraMainnetState, loan_entity_class=NostraMainnetLoanEntity)

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

    def calculate_health_ratio(self) -> defaultdict:
        """
        Calculates health ratio based on provided data.
        :return: A dictionary of the ready health ratio data.
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

        result_data = defaultdict()
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
                result_data.update({
                    f"{uuid.uuid4()}": {
                        USER_FIELD_NAME: user_id,
                        HEALTH_FACTOR_FIELD_NAME: health_ratio_level,
                        TIMESTAMP_FIELD_NAME: datetime.now().timestamp(),
                        PROTOCOL_FIELD_NAME: ProtocolIDs.NOSTRA_MAINNET.value
                    }
                })

        return result_data
