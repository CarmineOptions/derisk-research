import logging

import pandas as pd
from time import monotonic
from handlers.state import State
from handlers.loan_states.abstractions import LoanStateComputationBase
from handlers.loan_states.zklend.events import ZkLendState
from handler_tools.constants import ProtocolAddresses, ProtocolIDs

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
            # For each block number, process the interest rate event
            if (
                    self.last_block != block_number
                    and event["key_name"] in self.INTEREST_RATES_KEYS
            ):
                self.process_interest_rate_event(instance_state, event)

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

        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]
        sorted_df = df_filtered.sort_values(by=["block_number", "id"])

        for index, row in sorted_df.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(zklend_state, method_name, row)

        result_df = self.get_result_df(zklend_state.loan_entities)
        result_df["deposit"] = [
            {token: float(amount) for token, amount in loan.deposit.values.items()}
            for loan in zklend_state.loan_entities.values()
        ]
        return result_df

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 5
        default_last_block = self.last_block
        for protocol_address in self.PROTOCOL_ADDRESSES:
            retry = 0
            logger.info(f'Default last block: {default_last_block}')
            self.last_block = default_last_block

            while retry < max_retries:
                data = self.get_data(protocol_address, self.last_block)

                if not data:
                    logger.info(f"No data found for address {protocol_address} at block {self.last_block}")
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
