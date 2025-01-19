""" This module contains the zkLend loan state computation class. """
import logging
from time import monotonic

import pandas as pd
from data_handler.handler_tools.constants import ProtocolAddresses
from data_handler.handlers.loan_states.abstractions import LoanStateComputationBase
from data_handler.handlers.loan_states.zklend.events import ZkLendState
from data_handler.handlers.loan_states.zklend.utils import ZkLendInitializer
from shared.constants import ProtocolIDs
from shared.state import State

logger = logging.getLogger(__name__)


class ZkLendLoanStateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the zkLend protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.ZKLEND.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().ZKLEND_MARKET_ADDRESSES
    INTEREST_RATES_KEYS = [
        "AccumulatorsSync",
        "zklend::market::Market::AccumulatorsSync",
    ]

    def process_event(
        self, instance_state: State, method_name: str, event: pd.Series
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
            self.set_interest_rate(instance_state, block_number, self.PROTOCOL_TYPE)
            if block_number and block_number >= self.last_block:
                # For each block number, process the interest rate event
                if event["key_name"] in self.INTEREST_RATES_KEYS:
                    self.process_interest_rate_event(instance_state, event)

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

    def process_interest_rate_event(
        self, zklend_state: ZkLendState, event: pd.Series
    ) -> None:
        """
        Processes an interest rate event.

        :param zklend_state: The zkLend state object.
        :type zklend_state: ZkLendState
        :param event: The data of the event.
        :type event: pd.Series
        """
        zklend_state.process_accumulators_sync_event(event)
        self.add_interest_rate_data(zklend_state, event)

    def process_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Processes the data retrieved from the DeRisk API.
        This method must be implemented by subclasses to define the data processing steps.

        :param data: The data retrieved from the DeRisk API.
        :type data: list[dict]

        :return: pd.DataFrame
        """
        zklend_state = ZkLendState()
        events_mapping = zklend_state.EVENTS_METHODS_MAPPING
        # Init DataFrame
        df = pd.DataFrame(data)
        # Init collateral_enabled state via ZkLendInitializer
        zklend_initializer = ZkLendInitializer(zklend_state)
        user_ids = zklend_initializer.get_user_ids_from_df(df)
        zklend_initializer.set_last_loan_states_per_users(user_ids)
        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]
        sorted_df = df_filtered.sort_values(by=["block_number", "id"])

        for index, row in sorted_df.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(zklend_state, method_name, row)

        result_df = self.get_result_df(zklend_state.loan_entities)
        result_df["deposit"] = [
            {token: float(amount) for token, amount in loan.deposit.items()}
            for loan in zklend_state.loan_entities.values()
        ]
        logger.info(f"Processed data for block {self.last_block}")
        return result_df

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
            "user": [user for user in loan_entities.keys()],
            "collateral": [
                {token: float(amount) for token, amount in loan.collateral.items()}
                for loan in loan_entities_values
            ],
            "block": [entity.extra_info.block for entity in loan_entities_values],
            "timestamp": [
                entity.extra_info.timestamp for entity in loan_entities_values
            ],
            "debt": [
                {token: float(amount) for token, amount in loan.debt.items()}
                for loan in loan_entities_values
            ],
        }

        result_df = pd.DataFrame(result_dict)
        return result_df

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 5
        retry = 0
        zklend_protocol_address = self.PROTOCOL_ADDRESSES

        logger.info(f"Default last block: {self.last_block}")
        while retry < max_retries:
            data = self.get_data(zklend_protocol_address, self.last_block)

            if not data:
                logger.info(
                    f"No data found for address {zklend_protocol_address} at block {self.last_block}"
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
            logger.info(f"Reached max retries for address {zklend_protocol_address}")


def run_loan_states_computation_for_zklend() -> None:
    """
    Runs the zkLend loan state computation.
    """
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting zkLend loan state computation")
    computation = ZkLendLoanStateComputation()
    computation.run()

    logger.info(
        "Finished zkLend loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


if __name__ == "__main__":
    run_loan_states_computation_for_zklend()
