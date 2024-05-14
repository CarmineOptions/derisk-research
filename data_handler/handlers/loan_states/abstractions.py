import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd
from shared.constans import ProtocolIDs

from data_handler.database.crud import DBConnector
from data_handler.database.models import LoanState
from data_handler.tools.api_connector import DeRiskAPIConnector

logger = logging.getLogger(__name__)


class LoanStateComputationBase(ABC):
    """Base class for computing loan states based on data from a DeRisk API.

    Attributes:
        PROTOCOL_ADDRESSES (Dict[str, str]): A dictionary mapping protocol names to their addresses.
        PROTOCOL_TYPE (ProtocolIDs): The protocol ID as defined in the ProtocolIDs enum.
    """

    PROTOCOL_ADDRESSES: Optional[Dict[str, str]] = None
    PROTOCOL_TYPE: Optional[ProtocolIDs] = None
    PAGINATION_SIZE: int = 1000

    def __init__(self):
        """
        Initializes the loan state computation base with a DeRisk API connector and a placeholder
         for the last block.
        """
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = DBConnector()
        self.last_block = self.db_connector.get_last_block()

    @abstractmethod
    def get_data(self, form_address: str, min_block: int) -> dict:
        """
        Fetches data from the DeRisk API endpoint using the defined protocol address.
        This method must be implemented by subclasses to specify how data is retrieved from the API.

        :param form_address: The address of the contract from which to retrieve events.
        :type form_address: str
        :param min_block: The minimum block number from which to retrieve events.
        :type min_block: int
        """
        pass

    @abstractmethod
    def process_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Processes the data retrieved from the DeRisk API.
        This method must be implemented by subclasses to define the data processing steps.

        :param data: The data retrieved from the DeRisk API.
        :type data: list[dict]
        :return: pd.DataFrame
        """
        pass

    def save_data(self, df: pd.DataFrame) -> None:
        """
        Saves the processed data to the database.
        Ex
        """
        objects_to_write = []
        for index, item in df.iterrows():
            loan = LoanState(
                protocol_id=self.PROTOCOL_TYPE,
                user=item["user"],
                collateral=item["collateral"],
                debt=item["debt"],
                block=item["block"],
                timestamp=item["timestamp"],
            )
            objects_to_write.append(loan)
        self.db_connector.write_batch_to_db(objects_to_write)

    def process_event(
        self, instance_state: object, method_name: str, event: pd.Series
    ) -> None:
        """
        Processes an event based on the method name and the event data.

        Updates the last block processed to ensure data consistency
        and calls the appropriate method to handle the event.

        :param instance_state: The instance of the state class to call the method on.
        :type instance_state: object
        :param method_name: The name of the method to call for processing the event.
        :param event: The event data as a pandas Series.
        """
        try:
            block_number = event.get("block_number")
            if block_number and block_number >= self.last_block:
                self.last_block = block_number
                method = getattr(instance_state, method_name, None)
                if method:
                    method(event)
                else:
                    logger.info(
                        f"No method named {method_name} found for processing event."
                    )
        except Exception as e:
            logger.exception(f"Failed to process event due to an error: {e}")

    @abstractmethod
    def run(self) -> None:
        """
        Executes the computation steps: data retrieval, processing, and saving.

        This method orchestrates the whole computation process and must be implemented by subclasses.
        """
        pass
