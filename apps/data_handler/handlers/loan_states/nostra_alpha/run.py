""" This module contains the logic to compute the loan states for the NOSTRA_ALPHA protocol. """
import logging
from time import monotonic

import pandas as pd
from data_handler.handler_tools.constants import (
    NOSTRA_EVENTS_MAPPING,
    ProtocolAddresses,
)
from data_handler.handler_tools.nostra_alpha_settings import (
    NOSTRA_ALPHA_ADDRESSES_TO_EVENTS,
    NOSTRA_ALPHA_EVENTS_TO_METHODS,
    NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS,
)
from data_handler.handlers.loan_states.abstractions import LoanStateComputationBase
from data_handler.handlers.loan_states.nostra_alpha.events import NostraAlphaState

from shared.constants import ProtocolIDs

logger = logging.getLogger(__name__)
NOSTRA_ALPHA_EVENTS_TO_ORDER: dict[str, str] = {
    "InterestStateUpdated": 0,
    "Transfer": 1,
    "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer": 2,
    "Burn": 3,
    "Mint": 4,
}


class NostraAlphaStateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the NOSTRA_ALPHA protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.NOSTRA_ALPHA.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().NOSTRA_ALPHA_ADDRESSES
    INTEREST_RATES_KEYS = ["InterestStateUpdated"]
    EVENTS_MAPPING = NOSTRA_EVENTS_MAPPING
    EVENTS_METHODS_MAPPING = NOSTRA_ALPHA_EVENTS_TO_METHODS
    ADDRESSES_TO_EVENTS = NOSTRA_ALPHA_ADDRESSES_TO_EVENTS

    def process_interest_rate_event(self, nostra_state: NostraAlphaState, event: pd.Series) -> None:
        """
        Processes an interest rate event.

        :param nostra_state: The Nostra alpha state object.
        :type nostra_state: NostraAlphaState
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
        nostra_alpha_state = NostraAlphaState()

        events_with_interest_rate = (list(self.EVENTS_MAPPING.keys()) + self.INTEREST_RATES_KEYS)

        # Init DataFrame
        df = pd.DataFrame(data)
        df_filtered = df[df["key_name"].isin(events_with_interest_rate)]
        # Map 'key_name' to its corresponding order from the dict
        df_filtered["sort_order"] = df_filtered["key_name"].map(
            lambda x: NOSTRA_ALPHA_EVENTS_TO_ORDER.get(x, float("inf"))
        )

        # Sort by block_number, id, and the new 'sort_order' column
        sorted_df = df_filtered.sort_values(["block_number", "id", "sort_order"])

        # Drop the 'sort_order' column after sorting if it's not needed anymore
        sorted_df = sorted_df.drop(columns=["sort_order"])

        # Filter out events that are not in the mapping
        for index, row in sorted_df.iterrows():
            method_name = self.EVENTS_MAPPING.get(row["key_name"], "") or ""
            self.process_event(nostra_alpha_state, method_name, row)

        result_df = self.get_result_df(nostra_alpha_state.loan_entities)
        return result_df

    def process_event(
        self, instance_state: NostraAlphaState, method_name: str, event: pd.Series
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
            if event["from_address"] == NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS:
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

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 10000
        retry = 0
        self.last_block = 202336

        logger.info(f"Default last block: {self.last_block}")
        while retry < max_retries:
            interest_rate_data = self.get_data(
                NOSTRA_ALPHA_INTEREST_RATE_MODEL_ADDRESS, self.last_block
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


def run_loan_states_computation_for_nostra_alpha() -> None:
    """
    Runs the NOSTRA_ALPHA loan state computation.
    """
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting NostraAlpha loan state computation")
    computation = NostraAlphaStateComputation()
    computation.run()

    logger.info(
        "Finished NostraAlpha  loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


if __name__ == "__main__":
    run_loan_states_computation_for_nostra_alpha()
