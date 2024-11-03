""" This module contains the HashtackV0StateComputation 
class that computes the loan states for the HashstackV0 protocol. """

import logging
from time import monotonic

import pandas as pd
from data_handler.handler_tools.constants import ProtocolAddresses
from data_handler.handlers.loan_states.abstractions import (
    HashstackBaseLoanStateComputation,
)
from data_handler.handlers.loan_states.hashtack_v0.events import HashstackV0State
from data_handler.handlers.loan_states.hashtack_v0.utils import HashtackInitializer

from shared.constants import ProtocolIDs

logger = logging.getLogger(__name__)


class HashtackV0StateComputation(HashstackBaseLoanStateComputation):
    """
    A class that computes the loan states for the HashstackV0 protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.HASHSTACK_V0.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().HASHSTACK_V0_ADDRESSES

    def process_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Processes the data retrieved from the DeRisk API.
        This method must be implemented by subclasses to define the data processing steps.

        :param data: The data retrieved from the DeRisk API.
        :type data: list[dict]

        :return: pd.DataFrame
        """
        hashtack_v0_state = HashstackV0State()
        events_mapping = hashtack_v0_state.EVENTS_METHODS_MAPPING
        # Init DataFrame
        df = pd.DataFrame(data)

        # init HashtackInitializer
        hashtack_initializer = HashtackInitializer(hashtack_v0_state)
        loan_ids = hashtack_initializer.get_loan_ids(df)
        hashtack_initializer.set_last_loan_states_per_loan_ids(list(set(loan_ids)), version=0)

        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]

        for index, row in df_filtered.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(hashtack_v0_state, method_name, row)

        result_df = self.get_result_df(hashtack_v0_state.loan_entities)
        return result_df

    def process_event(self, instance_state: "State", method_name: str, event: pd.Series) -> None:
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
            # Process the event
            if block_number and block_number >= self.last_block:
                self.last_block = block_number
                method = getattr(instance_state, method_name, None)
                if method:
                    method(event)
                else:
                    logger.debug(f"No method named {method_name} found for processing event.")
            else:
                logger.debug(f"No InterestRate found for block number {block_number}")
        except Exception as e:
            logger.exception(f"Failed to process event due to an error: {e}")

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 10000  # FIXME change it after first run on the server
        retry = 0
        self.last_block = 21000  # FIXME change it after first run on the server

        logger.info(f"Default last block: {self.last_block}")
        while retry < max_retries:
            # FIXME add interest rate data
            data = self.get_addresses_data(self.PROTOCOL_ADDRESSES, self.last_block)

            if not data:
                logger.info(f"No data for block {self.last_block}")
                self.last_block += self.PAGINATION_SIZE
                retry += 1
                continue

            # Process the data
            processed_data = self.process_data(data)

            # Save the processed data and  interest rate data
            self.save_data(processed_data)
            # self.save_interest_rate_data()

            # Update the last block
            self.last_block += self.PAGINATION_SIZE
            logger.info(f"Processed data up to block {self.last_block}")
            retry = 0  # Reset retry counter if data is found and processed

        if retry == max_retries:
            logger.info(f"Reached max retries for block: {self.last_block}")


def run_loan_states_computation_for_hashstack_v0() -> None:
    """
    Runs the HashstackV0 loan state computation.
    """
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting Hashtack v0 loan state computation")
    computation = HashtackV0StateComputation()
    computation.run()

    logger.info(
        "Finished Hashtack v0 loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


if __name__ == "__main__":
    run_loan_states_computation_for_hashstack_v0()
