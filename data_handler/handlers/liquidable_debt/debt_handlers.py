import pandas as pd
from decimal import Decimal
from copy import deepcopy

from handlers.state import State
from db.crud import DBConnector
from db.models import LiquidableDebt

from handlers.liquidable_debt.bases import Collector
from handlers.liquidable_debt.collectors import GoogleCloudDataCollector
from handlers.liquidable_debt.values import (GS_BUCKET_URL, GS_BUCKET_NAME, LendingProtocolNames,
                                             LOCAL_STORAGE_PATH, COLLATERAL_FIELD_NAME, PROTOCOL_FIELD_NAME,
                                             DEBT_FIELD_NAME, USER_FIELD_NAME, RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME,
                                             HEALTH_FACTOR_FIELD_NAME, DEBT_USD_FIELD_NAME, FIELDS_TO_VALIDATE,
                                             ALL_NEEDED_FIELDS, LIQUIDABLE_DEBT_FIELD_NAME)
from handlers.loan_states.zklend.events import ZkLendState
from handlers.helpers import TokenValues


class GCloudLiquidableDebtDataHandler:
    """
    A handler that collects data from Google Cloud Storage bucket,
    parses it and stores it in the database.

    :cvar AVAILABLE_PROTOCOLS: A list of all available protocols.
    :method: `update_data` -> Updates the data stored in the database.:
    """
    AVAILABLE_PROTOCOLS = [item.value for item in LendingProtocolNames]
    CONNECTOR = DBConnector()

    def __init__(
            self,
            loan_state_class: State,
            connection_url: str = GS_BUCKET_URL,
            bucket_name: str = GS_BUCKET_NAME,
            collector: Collector = GoogleCloudDataCollector
    ):
        self.collector = collector
        self.connection_url = connection_url
        self.bucket_name = bucket_name
        self.state_class = loan_state_class

    def prepare_data(self, protocol_name: str, path: str = LOCAL_STORAGE_PATH) -> dict:
        uploaded_file_path = self.collector.collect_data(
            protocol_name=protocol_name,
            available_protocols=self.AVAILABLE_PROTOCOLS,
            bucket_name=self.bucket_name,
            path=path,
            url=self.connection_url
        )
        parsed_data = self._parse_file(uploaded_file_path)

        return self._calculate_liquidable_debt(parsed_data)

    def _calculate_liquidable_debt(self, data: dict = None):
        """
        Calculates liquidable debt based on data provided and updates an existing data.
        :param data: Data to calculate liquidable debt for.
        :return: A dictionary of the ready liquidable debt data.
        """
        result_data = deepcopy(data)

        for row_number in data:
            state = self.state_class(verbose_user=data[row_number][USER_FIELD_NAME])

            state.loan_entities[data[row_number][USER_FIELD_NAME]].debt.values = {
                key: value
                for key, value in data[row_number][DEBT_FIELD_NAME].items()
            }
            state.loan_entities[data[row_number][USER_FIELD_NAME]].collateral.values = {
                key: value
                for key, value in data[row_number][COLLATERAL_FIELD_NAME].items()
            }

            for token in data[row_number][DEBT_FIELD_NAME]:
                if not data[row_number][COLLATERAL_FIELD_NAME].get(token, ""):
                    continue

                result = state.compute_liquidable_debt_at_price(
                    prices=TokenValues(),
                    collateral_token=token,
                    collateral_token_price=data[row_number][COLLATERAL_FIELD_NAME][token],
                    debt_token=token,
                    risk_adjusted_collateral_usd=data[row_number][RISK_ADJUSTED_COLLATERAL_USD_FIELD_NAME],
                    debt_usd=data[row_number][DEBT_USD_FIELD_NAME],
                    health_factor=data[row_number][HEALTH_FACTOR_FIELD_NAME],
                )

                if result > Decimal("0"):
                    result_data[row_number][LIQUIDABLE_DEBT_FIELD_NAME] = result

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

        for row_number in data[USER_FIELD_NAME]:
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

    @staticmethod
    def _transform_str_into_dict(tokens: str) -> dict:
        """
        Transforms a string into a dictionary.
        :param tokens: The string to transform.
        :return: A dictionary of the transformed data.
        """
        result = dict()
        separeted_tokens = tokens.split(', ')
        for token_ in separeted_tokens:
            if "/" in token_:
                t = token_.split("/")[1]
                current_token, value = t.split(" Pool: ")
                token_index = separeted_tokens.index(token_)
                separeted_tokens[token_index] = f"{current_token}: {value}"

        for token_ in separeted_tokens:
            token, value = token_.split(': ')
            result.update({token: Decimal(value)})

        return result

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
