import pandas as pd
import uuid
import asyncio
import time
import os
from decimal import Decimal
from copy import deepcopy
from typing import Iterable

import requests
from dotenv import load_dotenv

from db.crud import DBConnector
from db.models import LiquidableDebt

from handlers.state import State
from handlers.liquidable_debt.bases import Collector
from handlers.liquidable_debt.collectors import GoogleCloudDataCollector
from handlers.liquidable_debt.exceptions import ProtocolExistenceError
from handlers.liquidable_debt.values import (GS_BUCKET_URL, GS_BUCKET_NAME, LendingProtocolNames,
                                             LOCAL_STORAGE_PATH, COLLATERAL_FIELD_NAME, PROTOCOL_FIELD_NAME,
                                             DEBT_FIELD_NAME, USER_FIELD_NAME, RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME,
                                             HEALTH_FACTOR_FIELD_NAME, DEBT_USD_FIELD_NAME, FIELDS_TO_VALIDATE,
                                             LIQUIDABLE_DEBT_FIELD_NAME, PRICE_FIELD_NAME,
                                             MYSWAP_VALUE, JEDISWAP_VALUE, POOL_SPLIT_VALUE, ROW_ID_FIELD_NAME)
from handlers.loan_states.zklend.events import ZkLendState, ZkLendLoanEntity
from handlers.loan_states.hashtack_v0.events import HashstackV0State
from handlers.loan_states.hashtack_v1.events import HashstackV1State
from handlers.state import InterestRateModels, LoanEntity
from handlers.liquidable_debt.utils import Prices
from handlers.settings import TOKEN_PAIRS
from handlers.helpers import TokenValues
from tools.constants import AvailableProtocolID

load_dotenv()


class GCloudLiquidableDebtDataHandler:
    """
    A handler that collects data from Google Cloud Storage bucket,
    parses it and stores it in the database.

    :cvar AVAILABLE_PROTOCOLS: A list of all available protocols.
    :method: `update_data` -> Updates the data stored in the database.:
    """
    AVAILABLE_PROTOCOLS = [item.value for item in LendingProtocolNames]
    CONNECTOR = DBConnector()
    INTEREST_MODEL_VALUES_URL = os.environ.get("INTEREST_MODEL_VALUES_URL")

    def __init__(
            self,
            loan_state_class: State,
            loan_entity_class: LoanEntity,
            connection_url: str = GS_BUCKET_URL,
            bucket_name: str = GS_BUCKET_NAME,
            collector: Collector = GoogleCloudDataCollector
    ):
        self.collector = collector
        self.connection_url = connection_url
        self.bucket_name = bucket_name
        self.state_class = loan_state_class
        self.loan_entity_class = loan_entity_class

    def prepare_data(self, protocol_name: str, path: str = LOCAL_STORAGE_PATH) -> dict:
        """
        Prepares the data for the given protocol.
        :param protocol_name: Protocol name.
        :param path: path to the file.
        :return: dict
        """
        uploaded_file_path = self.collector.collect_data(
            protocol_name=protocol_name,
            available_protocols=self.AVAILABLE_PROTOCOLS,
            bucket_name=self.bucket_name,
            path=path,
            url=self.connection_url
        )
        parsed_data = self._parse_file(uploaded_file_path)
        sorted_parsed_data = self._sort_by_token_pair_correspondence(parsed_data)

        return self._calculate_liquidable_debt(sorted_parsed_data)

    @staticmethod
    def _sort_by_token_pair_correspondence(
            parsed_data: dict = None,
    ) -> dict:
        """
        Sorts a given data by token pair correspondence.
        :param parsed_data: {
            Row number: {
                Field name: Token value
                 or Decimal - Field value (the price as example)
                 or {
                    Token name: Token value
                }
            }
        }
        :return: A dictionary of a sorted data.
        """
        result = deepcopy(parsed_data)
        for index, data in parsed_data.items():
            debt_tokens = data[DEBT_FIELD_NAME].keys()
            collateral_tokens = data[COLLATERAL_FIELD_NAME].keys()

            for collateral_token in collateral_tokens:
                if (not TOKEN_PAIRS.get(collateral_token) and
                        (set(collateral_tokens) & set(debt_tokens))):
                    del result[index][COLLATERAL_FIELD_NAME][collateral_token]

            if not result[index][COLLATERAL_FIELD_NAME].keys():
                del result[index]

        return result

    @staticmethod
    def get_prices_range(collateral_token_name: str, current_price: Decimal) -> Iterable[Decimal]:
        """
        Get prices range based on the current price.
        :param current_price: Decimal - The current pair price.
        :param collateral_token_name: str - The name of the collateral token.
        :return: Iterable[Decimal] - The iterable prices range.
        """
        from handlers.helpers import get_range, get_collateral_token_range

        collateral_tokens = ("ETH", "wBTC", "STRK")

        if collateral_token_name in collateral_tokens:
            return get_collateral_token_range(collateral_token_name, current_price)

        return get_range(Decimal(0), current_price * Decimal("1.3"), Decimal(current_price / 100))

    @classmethod
    def verify_endpoint_protocol(cls, protocol_name: str) -> None:
        """
        Verifies if the protocol exists
        :param protocol_name: str
        :return: None
        """
        if protocol_name.lower() not in [
            protocol.value.lower() for protocol in AvailableProtocolID
        ]:
            raise ProtocolExistenceError(protocol_name)

    @staticmethod
    def _get_response(protocol_name: str) -> requests.Response:
        """
        Gets the response from endpoint for the given protocol.
        :param protocol_name: str
        :return: requests.Response
        """
        response = requests.get(cls.INTEREST_MODEL_VALUES_URL.format(protocol=protocol_name))
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_interest_rate_models_data(cls, protocol_name: str) -> dict:
        """
        Returns an interest rate models data
        :param protocol_name: str
        :return: dict
        """
        cls.verify_endpoint_protocol(protocol_name)
        for protocol in AvailableProtocolID:
            current_protocol = str(protocol.value).lower()
            if protocol_name.lower() == current_protocol:
                try:
                    return cls._get_response(protocol.value)
                except:
                    time.sleep(10)
                    return cls._get_response(protocol.value)

    @staticmethod
    def normalize_protocol_name(protocol_name: str) -> str:
        """
        Normalizes the given protocol name.
        :param protocol_name: str
        :return: str
        """
        return "_".join(protocol_name.split(" ")).lower()

    def _calculate_liquidable_debt(
            self, data: dict = None,
    ) -> dict:
        """
        Calculates liquidable debt based on data provided and updates an existing data.
        Data to calculate liquidable debt for:
        :param data: {
            Row number: {
                Field name: Token value
                 or Decimal - Field value (the price as example)
                 or {
                    Token name: Token value
                }
            }
        }
        :return: A dictionary of the ready liquidable debt data.
        """
        result_data = dict()
        current_prices = Prices()
        asyncio.run(current_prices.get_lp_token_prices())
        INTEREST_RATE_MODELS_MAPPING = {
            protocol.value.lower(): self.get_interest_rate_models_data(protocol_name=protocol.value)
            for protocol in AvailableProtocolID
        }

        for index, row in data.items():
            # even if it isn't per-user data, we need to provide a user ID
            # so like that we're able to provide debt and collateral values
            user_wallet_id = row[USER_FIELD_NAME]
            state = self.state_class(verbose_user=user_wallet_id)
            normalized_protocol_name = self.normalize_protocol_name(row[PROTOCOL_FIELD_NAME])
            interest_rate_models = INTEREST_RATE_MODELS_MAPPING.get(normalized_protocol_name)
            debt_token = next(iter(row[DEBT_FIELD_NAME].keys()))

            for collateral_token in row[COLLATERAL_FIELD_NAME].keys():
                hypothetical_collateral_token_prices = self.get_prices_range(
                    collateral_token_name=collateral_token,
                    current_price=current_prices.prices.values[collateral_token]
                )

                # Set up collateral and debt interest rate models
                state.collateral_interest_rate_models = InterestRateModels(
                    values=interest_rate_models[COLLATERAL_FIELD_NAME.lower()]
                )
                state.debt_interest_rate_models = InterestRateModels(
                    values=interest_rate_models[DEBT_FIELD_NAME.lower()]
                )

                for hypothetical_price in hypothetical_collateral_token_prices:
                    current_prices.prices.values[collateral_token] = hypothetical_price

                    if not isinstance(state, (HashstackV0State, HashstackV1State)):
                        state.loan_entities[user_wallet_id].debt.values = {
                            debt_token: hypothetical_price
                            for debt_token in TOKEN_PAIRS.get(collateral_token, "")
                        }
                        state.loan_entities[user_wallet_id].collateral.values = {
                            collateral_token: hypothetical_price
                        }

                    liquidable_debt = state.compute_liquidable_debt_at_price(
                        prices=TokenValues(init_value=current_prices.prices.values.get(collateral_token)),
                        collateral_token=collateral_token,
                        collateral_token_price=hypothetical_price,
                        debt_token=debt_token,
                    )

                    if liquidable_debt > Decimal("0"):
                        result_data.update({
                            f"{uuid.uuid4()}": {
                                LIQUIDABLE_DEBT_FIELD_NAME: liquidable_debt,
                                PRICE_FIELD_NAME: hypothetical_price,
                                COLLATERAL_FIELD_NAME: collateral_token,
                                PROTOCOL_FIELD_NAME: row[PROTOCOL_FIELD_NAME],
                                DEBT_FIELD_NAME: debt_token,
                            }
                        })

        return result_data

    @classmethod
    def _parse_file(cls, path: str = None) -> dict:
        """
        Parse a parquet file into a dictionary.
        :param path: The path to the parquet file.
        :return: A dictionary of the parsed data.
        """
        data = pd.read_parquet(path=path).to_dict()
        arranged_data = cls._arrange_data_by_row(data)

        for row_number in arranged_data:
            arranged_data[row_number][DEBT_FIELD_NAME] = cls._transform_str_into_dict(
                arranged_data[row_number][DEBT_FIELD_NAME]
            )
            arranged_data[row_number][COLLATERAL_FIELD_NAME] = cls._transform_str_into_dict(
                arranged_data[row_number][COLLATERAL_FIELD_NAME]
            )

        return arranged_data

    @classmethod
    def _arrange_data_by_row(cls, data: dict = None) -> dict:
        """
        Arranges the dictionary data by rows.
        :param data: The dictionary to arrange.
        :return: A dictionary of the arranged data.
        """
        result = dict()

        for row_number in data[DEBT_FIELD_NAME]:
            arranged_row = {
                USER_FIELD_NAME: data[USER_FIELD_NAME][row_number],
                PROTOCOL_FIELD_NAME: data[PROTOCOL_FIELD_NAME][row_number],
                RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME: data[RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME][row_number],
                DEBT_USD_FIELD_NAME: data[DEBT_USD_FIELD_NAME][row_number],
                HEALTH_FACTOR_FIELD_NAME: data[HEALTH_FACTOR_FIELD_NAME][row_number],
                COLLATERAL_FIELD_NAME: data[COLLATERAL_FIELD_NAME][row_number],
                DEBT_FIELD_NAME: data[DEBT_FIELD_NAME][row_number],
            }
            if cls._is_valid(arranged_row):
                result.update({row_number: arranged_row})

        return result

    @staticmethod
    def _is_valid(data: dict = None) -> bool:
        """
        Checks if the dictionary data is valid.
        :param data: The dictionary to check.
        :return: True if the dictionary data is valid, False otherwise.
        """
        for field in FIELDS_TO_VALIDATE:
            if not data[field]:
                return False

            if not isinstance(data[field], str):
                if data[field] <= Decimal("0") \
                        or data[field] == Decimal("inf"):
                    return False

        return True

    @classmethod
    def _transform_str_into_dict(cls, tokens: str) -> dict:
        """
        Transforms a string into a dictionary.
        :param tokens: The string to transform.
        :return: A dictionary of the transformed data.
        """
        result = dict()
        separated_tokens = tokens.split(', ')

        for token in separated_tokens:
            if not token:
                continue

            if MYSWAP_VALUE in token:
                current_token, value = cls.split_collateral(
                    token, f"{MYSWAP_VALUE}: "
                ).split(POOL_SPLIT_VALUE)
                result.update({current_token: Decimal(value)})

                continue

            if JEDISWAP_VALUE in token:
                current_token, value = cls.split_collateral(
                    token, f"{JEDISWAP_VALUE}: "
                ).split(POOL_SPLIT_VALUE)
                result.update({current_token: Decimal(value)})

                continue

            token, value = token.split(': ')
            result.update({token: Decimal(value)})

        return result

    @staticmethod
    def split_collateral(collateral_string: str, platform_name: str) -> str:
        """
        Removes a platform name from the collateral string.
        :param collateral_string: The collateral string to split.
        :param platform_name: The platform name.
        :return: A collateral string without the platform name.
        """
        result = collateral_string.split(platform_name)
        result.remove("")
        return next(iter(result))

    @classmethod
    def _write_to_db(cls, data: dict = None) -> None:
        """
        Writes the data into the database.
        :param data: A dictionary of the parsed data.
        :return: None
        """
        cls.CONNECTOR.write_to_db(LiquidableDebt(**data))


class DBLiquidableDebtDataHandler:
    # TODO write logic when it will be needed
    pass
