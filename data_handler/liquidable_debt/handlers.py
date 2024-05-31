import dask.dataframe as dd
import pandas as pd

# from handlers.state import State
from data_handler.database.crud import DBConnector
from data_handler.database.models import LiquidableDebt

from .bases import Collector
from .collectors import GoogleCloudDataCollector
from data_handler.liquidable_debt.values import (GS_BUCKET_URL, GS_BUCKET_NAME, LendingProtocolNames,
                     LOCAL_STORAGE_PATH, PARQUET_FILE_FIELDS_TO_PARSE, COLLATERAL_FIELD_NAME)


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
            # loan_state: State,
            connection_url: str = GS_BUCKET_URL,
            bucket_name: str = GS_BUCKET_NAME,
            collector: Collector = GoogleCloudDataCollector
    ):
        self.collector = collector
        self.connection_url = connection_url
        self.bucket_name = bucket_name
        # self.state = loan_state

    def transform_data(self, protocol_name: str, path: str = LOCAL_STORAGE_PATH):
        uploaded_file_path = self.collector.collect_data(
            protocol_name=protocol_name,
            available_protocols=self.AVAILABLE_PROTOCOLS,
            bucket_name=self.bucket_name,
            path=path,
            url=self.connection_url
        )
        parsed_data = self.parse_file(uploaded_file_path)
        # return prepare_data(data)

    @staticmethod
    def parse_file(path: str = None) -> dict:
        """
        Parse a parquet file into a dictionary.
        :param path: The path to the parquet file.
        :return: A dictionary of the parsed data.
        """
        data = pd.read_parquet(path=path).to_dict()
        result = dict()

        for key in PARQUET_FILE_FIELDS_TO_PARSE:
            if key == COLLATERAL_FIELD_NAME:
                collaterals = {
                    key_: key[key_]
                    for key_ in key[COLLATERAL_FIELD_NAME]
                }
                result.update({COLLATERAL_FIELD_NAME: collaterals})

                continue

            result.update({key: data[key]})

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
