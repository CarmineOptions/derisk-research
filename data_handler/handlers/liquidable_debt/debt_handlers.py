import pandas as pd
from decimal import Decimal

# from handlers.state import State
from database.crud import DBConnector
from database.models import LiquidableDebt

from bases import Collector
from collectors import GoogleCloudDataCollector
from handlers.liquidable_debt.values import (GS_BUCKET_URL, GS_BUCKET_NAME, LendingProtocolNames,
                                             LOCAL_STORAGE_PATH, PARQUET_FILE_FIELDS_TO_PARSE,
                                             COLLATERAL_FIELD_NAME, PROTOCOL_FIELD_NAME)


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
            # loan_state: State,  # State inherited class isntance
            connection_url: str = GS_BUCKET_URL,
            bucket_name: str = GS_BUCKET_NAME,
            collector: Collector = GoogleCloudDataCollector
    ):
        self.collector = collector
        self.connection_url = connection_url
        self.bucket_name = bucket_name
        # self.state = loan_state

    def prepare_data(self, protocol_name: str, path: str = LOCAL_STORAGE_PATH):
        uploaded_file_path = self.collector.collect_data(
            protocol_name=protocol_name,
            available_protocols=self.AVAILABLE_PROTOCOLS,
            bucket_name=self.bucket_name,
            path=path,
            url=self.connection_url
        )
        parsed_data = self._parse_file(uploaded_file_path)

    # def _calculate_liquidable_debt(self, parsed_data: dict):
    #     self.state.compute_liquidable_debt_at_price(
    #         prices=...,
    #         collateral_token=...,
    #         collateral_token_price=...,
    #         debt_token=...,
    #     )

    @classmethod
    def _parse_file(cls, path: str = None) -> dict:
        """
        Parse a parquet file into a dictionary.
        :param path: The path to the parquet file.
        :return: A dictionary of the parsed data.
        """
        data = pd.read_parquet(path=path).to_dict()
        result = dict()

        for field in PARQUET_FILE_FIELDS_TO_PARSE:
            if field == PROTOCOL_FIELD_NAME:
                result.update({field: PROTOCOL_FIELD_NAME})

            if field == COLLATERAL_FIELD_NAME:
                collaterals = {field: dict()}

                for key in data[field]:
                    if tokens := data[field][key]:
                        tokens_dict = cls._transform_str_into_dict(tokens)

                        collaterals[field].update({key: tokens_dict})

                result.update(**collaterals)

                continue

            result.update({field: data[field]})

        return result

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


from pprint import pprint

if __name__ == '__main__':
    handler = GCloudLiquidableDebtDataHandler()
    parsed_data = handler._parse_file(path="loans.parquet")
    pprint(parsed_data)
