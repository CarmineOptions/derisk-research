""" This module contains the base class for computing loan states 
based on data from a DeRisk API. """
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd
from data_handler.handler_tools.api_connector import DeRiskAPIConnector

from data_handler.db.crud import DBConnector
from data_handler.db.models import InterestRate, LoanState
from shared.constants import ProtocolIDs
from shared.state import State
from shared.types import InterestRateModels

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
    INTEREST_RATES_KEYS: list = []

    def __init__(self):
        """
        Initializes the loan state computation base with a DeRisk API connector and a placeholder
         for the last block.
        """
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = DBConnector()
        self.last_block = self.db_connector.get_last_block(self.PROTOCOL_TYPE)
        self.interest_rate_result: list = []

    def process_interest_rate_event(self, instance_state: State, event: pd.Series) -> None:
        """
        Processes an interest rate event.

        :param instance_state: The instance of the state class to call the method on.
        :type instance_state: object
        :param event: The data of the event.
        :type event: pd.Series
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

    def process_event(self, instance_state: State, method_name: str, event: pd.Series) -> None:
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
            self.set_interest_rate(instance_state, block_number, self.PROTOCOL_TYPE)

            if block_number and block_number >= self.last_block:
                self.last_block = block_number
                method = getattr(instance_state, method_name, None)
                if method:
                    method(event)
                else:
                    logger.debug(f"No method named {method_name} found for processing event.")
        except Exception as e:
            logger.exception(f"Failed to process event due to an error: {e}")

    def get_data(self, from_address: str, min_block: int) -> list:
        """
        Fetches data from the DeRisk API endpoint using the defined protocol address.
        This method must be implemented by subclasses to specify how data is retrieved from the API.

        :param from_address: The address of the contract from which to retrieve events.
        :type from_address: str
        :param min_block: The minimum block number from which to retrieve events.
        :type min_block: int
        """
        logger.info(
            f"Fetching data from {self.last_block} to {min_block + self.PAGINATION_SIZE} for address {from_address}"
        )
        return self.api_connector.get_data(
            from_address=from_address,
            min_block_number=self.last_block,
            max_block_number=min_block + self.PAGINATION_SIZE,
        )

    def get_addresses_data(self, from_addresses: list[str], min_block: int) -> list[dict]:
        """
        Fetches data from the DeRisk API endpoint using the defined protocol address.
        This method must be implemented by subclasses to specify how data is retrieved from the API.

        :param from_addresses: The addresses of the contract from which to retrieve events.
        :type from_addresses: list[str]
        :param min_block: The minimum block number from which to retrieve events.
        :type min_block: int
        """
        logger.info(
            f"Fetching data from {self.last_block} to {min_block + self.PAGINATION_SIZE} for addresses {from_addresses}"
        )
        result_data: list = []
        for from_address in from_addresses:
            result_data.extend(self.get_data(from_address, min_block))

        return result_data

    def save_data(self, df: pd.DataFrame) -> None:
        """
        Saves the processed data to the database.
        Ex
        """
        if df.empty:
            logger.info("No data to save.")
            return

        objects_to_write = []
        for index, item in df.iterrows():
            loan = LoanState(
                protocol_id=self.PROTOCOL_TYPE,
                user=str(item["user"]),
                collateral=item["collateral"],
                debt=item["debt"],
                block=item["block"],
                timestamp=item["timestamp"],
                deposit=item.get("deposit"),
            )
            objects_to_write.append(loan)
        self.db_connector.write_loan_states_to_db(objects_to_write)

    def save_interest_rate_data(self) -> None:
        """
        Saves the interest rate data to the database.
        """
        if not self.interest_rate_result:
            logger.info("No interest rate data to save.")
            return

        objects_to_write = []
        for item in self.interest_rate_result:
            loan = InterestRate(
                protocol_id=self.PROTOCOL_TYPE,
                collateral=item["collateral"],
                debt=item["debt"],
                block=item["block"],
                timestamp=item["timestamp"],
            )
            objects_to_write.append(loan)
        self.db_connector.write_batch_to_db(objects_to_write)

    def get_result_df(self, loan_entities: dict) -> pd.DataFrame:
        """
        Creates a DataFrame with the loan state based on the loan entities.
        :param loan_entities: dictionary of loan entities
        :return: dataframe with loan state
        """
        # Create a DataFrame with the loan state
        loan_entities_values = loan_entities.values()
        if hasattr(loan_entities_values, "update_deposit"):
            for loan_entity in loan_entities_values:
                loan_entity.update_deposit()

        result_dict = {
            "protocol": [self.PROTOCOL_TYPE for _ in loan_entities_values],
            "user": [loan_entity.user for loan_entity in loan_entities_values],
            "collateral": [
                {
                    token: float(amount)
                    for token, amount in loan.collateral.values.items()
                } for loan in loan_entities_values
            ],
            "block": [entity.extra_info.block for entity in loan_entities_values],
            "timestamp": [entity.extra_info.timestamp for entity in loan_entities_values],
            "debt": [
                {
                    token: float(amount)
                    for token, amount in loan.debt.values.items()
                } for loan in loan_entities_values
            ],
        }
        result_df = pd.DataFrame(result_dict)
        return result_df

    def add_interest_rate_data(self, state_instance: State, event: pd.Series) -> None:
        """
        Adds interest rate data to the state instance.
        :param state_instance: The state instance to add the data to.
        :param event: The event data.
        """
        self.interest_rate_result.append(
            {
                "block": event["block_number"],
                "timestamp": event["timestamp"],
                "debt": {
                    token: float(amount)
                    for token, amount in state_instance.interest_rate_models.debt.items()
                },
                "collateral": {
                    token: float(amount)
                    for token, amount in state_instance.interest_rate_models.collateral.items()
                },
            }
        )

    def set_interest_rate(self, instance_state: State, block: int, protocol_type: str) -> None:
        """
        Sets the interest rate for the zkLend protocol.

        :param instance_state: The zkLend|HashtackV0|HashtackV1 state object.
        :type instance_state: zkLend|HashtackV0|HashtackV1
        :param protocol_type: The protocol type.
        :type protocol_type: str
        :param block: block_number
        :type block: int
        """
        if block == instance_state.last_interest_rate_block_number:
            return

        interest_rate_data = self.db_connector.get_interest_rate_by_block(
            block_number=block, protocol_id=protocol_type
        )
        if (interest_rate_data
                and instance_state.last_interest_rate_block_number != interest_rate_data.block):
            (
                collateral_interest_rate,
                debt_interest_rate,
            ) = interest_rate_data.get_json_deserialized()
            instance_state.interest_rate_models.collateral = InterestRateModels(
                collateral_interest_rate
            )
            instance_state.interest_rate_models.debt = InterestRateModels(debt_interest_rate)
            instance_state.last_interest_rate_block_number = block

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 5
        default_last_block = self.last_block
        for protocol_address in self.PROTOCOL_ADDRESSES:
            retry = 0
            logger.info(f"Default last block: {default_last_block}")

            self.last_block = default_last_block

            while retry < max_retries:
                data = self.get_data(protocol_address, self.last_block)

                if not data:
                    logger.info(
                        f"No data found for address {protocol_address} at block {self.last_block}"
                    )
                    self.last_block += self.PAGINATION_SIZE
                    retry += 1
                    continue

                processed_data = self.process_data(data)
                self.save_data(processed_data)
                self.save_interest_rate_data()
                self.last_block += self.PAGINATION_SIZE
                logger.info(f"Processed data up to block {self.last_block}")
                retry = 0  # Reset retry counter if data is found and processed

            if retry == max_retries:
                logger.info(f"Reached max retries for address {protocol_address}")


class HashstackBaseLoanStateComputation(LoanStateComputationBase):
    """Class for computing loan states for the Hashstack V0/V1 protocols."""

    def get_result_df(self, loan_entities: dict) -> pd.DataFrame:
        """
        Creates a DataFrame with the loan state based on the loan entities.
        :param loan_entities: dictionary of loan entities
        :return: dataframe with loan state
        """

        # if there are no loan entities, return an empty DataFrame
        if not loan_entities:
            return pd.DataFrame()

        filtered_loan_entities: dict = {}
        # remove objects from loan_entities_values if the object has `has_skip` attribute
        for loan_id, loan_entity in loan_entities.items():
            has_skip = getattr(loan_entity, "has_skip", None)
            if not has_skip:
                filtered_loan_entities[loan_id] = loan_entity

        result_dict = {
            "protocol": [self.PROTOCOL_TYPE for _ in filtered_loan_entities.keys()],
            "user": [loan_entity.user for loan_entity in filtered_loan_entities.values()],
            "collateral": [
                {
                    token: float(amount)
                    for token, amount in loan.collateral.values.items()
                } for loan in filtered_loan_entities.values()
            ],
            "block": [entity.extra_info.block for entity in filtered_loan_entities.values()],
            "timestamp":
            [entity.extra_info.timestamp for entity in filtered_loan_entities.values()],
            "debt": [
                {
                    token: float(amount)
                    for token, amount in loan.debt.values.items()
                } for loan in filtered_loan_entities.values()
            ],
        }

        result_df = pd.DataFrame(result_dict)
        return result_df
