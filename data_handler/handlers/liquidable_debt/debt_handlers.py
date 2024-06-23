import pandas as pd
import uuid
import asyncio
import time
import os
from decimal import Decimal
from copy import deepcopy
from typing import Iterable

import requests

from db.crud import DBConnector
from db.models import LiquidableDebt, LoanState

from handlers.state import State, InterestRateModels, LoanEntity
from handlers.liquidable_debt.bases import Collector
from handlers.liquidable_debt.collectors import GoogleCloudDataCollector
from handlers.liquidable_debt.exceptions import ProtocolExistenceError
from handlers.liquidable_debt.values import (GS_BUCKET_URL, GS_BUCKET_NAME, LendingProtocolNames,
                                             LOCAL_STORAGE_PATH, COLLATERAL_FIELD_NAME, PROTOCOL_FIELD_NAME,
                                             DEBT_FIELD_NAME, USER_FIELD_NAME, RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME,
                                             HEALTH_FACTOR_FIELD_NAME, DEBT_USD_FIELD_NAME, FIELDS_TO_VALIDATE,
                                             LIQUIDABLE_DEBT_FIELD_NAME, PRICE_FIELD_NAME,
                                             MYSWAP_VALUE, JEDISWAP_VALUE, POOL_SPLIT_VALUE, ROW_ID_FIELD_NAME)
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity, TokenSettings
from handlers.liquidable_debt.utils import Prices
from handlers.settings import TOKEN_PAIRS
from handlers.helpers import TokenValues, get_range, get_collateral_token_range
from handler_tools.constants import AvailableProtocolID


class DBLiquidableDebtDataHandler:
    """
    A handler that collects data from the DB,
    computes the liquidable debt and stores it in the database.

    :cvar AVAILABLE_PROTOCOLS: A list of all available protocols.
    :cvar CONNECTOR: Connector used to connect to the database.
    :cvar INTEREST_MODEL_VALUES_URL: URL for interests model values.
    """
    AVAILABLE_PROTOCOLS = [item.value for item in LendingProtocolNames]
    CONNECTOR = DBConnector()

    def __init__(
            self,
            loan_state_class: State,
            loan_entity_class: LoanEntity,
    ):
        self.state_class = loan_state_class
        self.loan_entity_class = loan_entity_class

    def fetch_data(self, protocol_name: str) -> tuple:
        """
        Prepares the data for the given protocol.
        :param protocol_name: Protocol name.
        :return: tuple
        """
        fetched_data = self.get_data_from_db(
            protocol_name=protocol_name
        )
        interest_rate_models = self.get_interest_rate_models_from_db(
            protocol_id=protocol_name
        )

        return fetched_data, interest_rate_models

    @staticmethod
    def get_prices_range(collateral_token_name: str, current_price: Decimal) -> Iterable[Decimal]:
        """
        Get prices range based on the current price.
        :param current_price: Decimal - The current pair price.
        :param collateral_token_name: str - The name of the collateral token.
        :return: Iterable[Decimal] - The iterable prices range.
        """
        collateral_tokens = TOKEN_PAIRS.keys()

        if collateral_token_name in collateral_tokens:
            return get_collateral_token_range(collateral_token_name, current_price)

        return get_range(Decimal(0), current_price * Decimal("1.3"), Decimal(current_price / 100))

    def calculate_liquidable_debt(self, protocol_name: str = None) -> dict:
        """
        Calculates liquidable debt based on data provided and updates an existing data.
        Data to calculate liquidable debt for:
        :param protocol_name: str
        :return: A dictionary of the ready liquidable debt data.
        """
        data, interest_rate_models = self.fetch_data(protocol_name=protocol_name)
        state = self.state_class()

        for instance in data:
            loan_entity = ZkLendLoanEntity()

            loan_entity.debt = TokenValues(values=instance.debt)
            loan_entity.collateral = TokenValues(values=instance.collateral)

            state.loan_entities.update(
                {
                    instance.user: loan_entity,
                }
            )

        # Set up collateral and debt interest rate models
        state.collateral_interest_rate_models = InterestRateModels(
            init_value=Decimal(interest_rate_models.collateral.get("STRK", ""))
        )
        state.debt_interest_rate_models = InterestRateModels(
            init_value=Decimal(interest_rate_models.debt.get("USDC", ""))
        )

        current_prices = Prices()
        asyncio.run(current_prices.get_lp_token_prices())

        hypothetical_collateral_token_prices = self.get_prices_range(
            collateral_token_name="STRK",
            current_price=current_prices.prices.values["STRK"]
        )

        result_data = dict()
        # Go through first hypothetical prices and then through the debts
        for hypothetical_price in hypothetical_collateral_token_prices:
            liquidable_debt = state.compute_liquidable_debt_at_price(
                prices=TokenValues(values=current_prices.prices.values),
                collateral_token="STRK",
                collateral_token_price=hypothetical_price,
                debt_token="USDC",
            )

            if liquidable_debt > Decimal("0"):
                result_data.update({
                        f"{uuid.uuid4()}": {
                            LIQUIDABLE_DEBT_FIELD_NAME: liquidable_debt,
                            PRICE_FIELD_NAME: hypothetical_price,
                            COLLATERAL_FIELD_NAME: "STRK",
                            PROTOCOL_FIELD_NAME: "zkLend",
                            DEBT_FIELD_NAME: "USDC",
                        }
                    })

        return result_data

    @classmethod
    def get_interest_rate_models_from_db(cls, protocol_id: str) -> dict:
        """
        Returns interest rate models data from DB.
        :param protocol_id: str
        :return: dict
        """
        return cls.CONNECTOR.get_last_interest_rate_record_by_protocol_id(protocol_id=protocol_id)

    @classmethod
    def get_data_from_db(cls, protocol_name: str) -> dict:
        """
        Gets the data from the database based on the protocol name.
        :param protocol_name: The protocol name.
        :return: The data from the database.
        """
        return cls.CONNECTOR.get_loans(
            model=LoanState,
            protocol=protocol_name
        )

    @classmethod
    def write_to_db(cls, data: LiquidableDebt = None) -> None:
        """
        Writes the data into the database.
        :param data: A dictionary of the parsed data.
        :return: None
        """
        cls.CONNECTOR.write_to_db(data)
