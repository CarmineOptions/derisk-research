""" This module contains the Nostra Mainnet loan state computation class. """
import logging
from time import monotonic

import pandas as pd
from data_handler.handler_tools.constants import (
    NOSTRA_EVENTS_MAPPING,
    ProtocolAddresses,
)
from data_handler.handler_tools.nostra_mainnet_settings import (
    NOSTRA_MAINNET_ADDRESSES_TO_EVENTS,
    NOSTRA_MAINNET_EVENTS_TO_METHODS,
    NOSTRA_MAINNET_EVENTS_TO_ORDER,
    NOSTRA_MAINNET_INTEREST_RATE_MODEL_ADDRESS,
)
from data_handler.handlers.loan_states.abstractions import LoanStateComputationBase
from data_handler.handlers.loan_states.nostra_mainnet.events import NostraMainnetState

from shared.constants import ProtocolIDs

logger = logging.getLogger(__name__)


class NostraMainnetStateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the Nostra Mainnet protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.NOSTRA_MAINNET.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().NOSTRA_MAINNET_ADDRESSES
    INTEREST_RATES_KEYS = ["InterestStateUpdated"]
    EVENTS_METHODS_MAPPING = NOSTRA_MAINNET_EVENTS_TO_METHODS
    ADDRESSES_TO_EVENTS = (NOSTRA_MAINNET_ADDRESSES_TO_EVENTS, )

    EVENTS_MAPPING = NOSTRA_EVENTS_MAPPING

    def process_event(
        self, instance_state: NostraMainnetState, method_name: str, event: pd.Series
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
            # For each block number, process the interest rate event
            if event["from_address"] == NOSTRA_MAINNET_INTEREST_RATE_MODEL_ADDRESS:
                self.process_interest_rate_event(instance_state, event)
                return

            if block_number and block_number >= self.last_block:
                self.last_block = block_number
                event_type = self.ADDRESSES_TO_EVENTS[event["from_address"]]
                getattr(
                    instance_state,
                    self.EVENTS_METHODS_MAPPING[(event_type, event["key_name"])],
                )(event=event)
        except Exception as e:
            logger.exception(f"Failed to process event due to an error: {e}")

    def process_interest_rate_event(
        self, nostra_state: NostraMainnetState, event: pd.Series
    ) -> None:
        """
        Processes an interest rate event.

        :param nostra_state: The Nostra Mainnet state object.
        :type nostra_state: Nostra Mainnet State
        :param event: The data of the event.
        :type event: pd.Series
        """
        nostra_state.process_interest_rate_model_event(event)
        self.add_interest_rate_data(nostra_state, event)

    def process_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Processes the data retrieved from the DeRisk API.
        This method must be implemented by subclasses to define the data processing steps.

        :param data: The data retrieved from the DeRisk API.
        :type data: list[dict]

        :return: pd.DataFrame
        """
        nostra_mainnet_state = NostraMainnetState()
        events_with_interest_rate = (list(self.EVENTS_MAPPING.keys()) + self.INTEREST_RATES_KEYS)

        # Init DataFrame
        df = pd.DataFrame(data)
        df_filtered = df[df["key_name"].isin(events_with_interest_rate)]

        # Map 'key_name' to its corresponding order from the dict
        df_filtered["sort_order"] = df_filtered["key_name"].map(
            lambda x: NOSTRA_MAINNET_EVENTS_TO_ORDER.get(x, float("inf"))
        )
        sorted_df = df_filtered.sort_values(["block_number", "id"])

        # Filter out events that are not in the mapping
        for index, row in sorted_df.iterrows():
            self.process_event(nostra_mainnet_state, None, row)

        result_df = self.get_result_df(nostra_mainnet_state.loan_entities)
        return result_df

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 5
        retry = 0

        logger.info(f"Default last block: {self.last_block}")

        while retry < max_retries:
            interest_rate_data = self.get_data(
                NOSTRA_MAINNET_INTEREST_RATE_MODEL_ADDRESS, self.last_block
            )
            data = self.get_addresses_data(self.PROTOCOL_ADDRESSES, self.last_block)

            if not data:
                logger.info(f"No data for block {self.last_block}")
                self.last_block += self.PAGINATION_SIZE
                retry += 1
                continue

            # Process the data
            all_events_data = interest_rate_data + data
            processed_data = self.process_data(all_events_data)

            # Save the processed data and  interest rate data
            self.save_data(processed_data)
            self.save_interest_rate_data()

            # Update the last block
            self.last_block += self.PAGINATION_SIZE
            logger.info(f"Processed data up to block {self.last_block}")
            retry = 0  # Reset retry counter if data is found and processed

        if retry == max_retries:
            logger.info(f"Reached max retries for block: {self.last_block}")


def run_loan_states_computation_for_nostra_mainnet() -> None:
    """
    Runs the Nostra Mainnet loan state computation.
    """
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting Nostra Mainnet  loan state computation")
    computation = NostraMainnetStateComputation()
    computation.run()

    logger.info(
        "Finished Nostra Mainnet loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


if __name__ == "__main__":
    run_loan_states_computation_for_nostra_mainnet()
