import logging

import pandas as pd
from time import monotonic
from data_handler.handlers.loan_states.abstractions import LoanStateComputationBase
from data_handler.handlers.loan_states.zklend.events import ZkLendState
from data_handler.tools.constants import ProtocolAddresses, ProtocolIDs

logger = logging.getLogger(__name__)


class ZkLendLoanStateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the zkLend protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.ZKLEND.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().ZKLEND_MARKET_ADDRESSES

    def get_data(self, form_address: str, min_block: int) -> dict:
        """
        Fetches data from the DeRisk API endpoint using the defined protocol address.
        This method must be implemented by subclasses to specify how data is retrieved from the API.

        :param form_address: The address of the contract from which to retrieve events.
        :type form_address: str
        :param min_block: The minimum block number from which to retrieve events.
        :type min_block: int
        """
        logger.info(
            f"Fetching data from {self.last_block} to {min_block + self.PAGINATION_SIZE} for address {form_address}"
        )
        return self.api_connector.get_data(
            from_address=form_address,
            min_block_number=self.last_block,
            max_block_number=min_block + self.PAGINATION_SIZE,
        )

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
        for index, row in df_filtered.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(zklend_state, method_name, row)

        loan_entities = zklend_state.loan_entities
        loan_entities_values = loan_entities.values()
        # Create a DataFrame with the loan state
        result_df = pd.DataFrame(
            {
                "protocol": [self.PROTOCOL_TYPE for _ in loan_entities.keys()],
                "user": [user for user in loan_entities],
                "collateral": [
                    {
                        token: float(amount)
                        for token, amount in loan.collateral.values.items()
                    }
                    for loan in loan_entities.values()
                ],
                "block": [entity.extra_info.block for entity in loan_entities_values],
                "timestamp": [entity.extra_info.timestamp for entity in loan_entities_values],
                "debt": [
                    {token: float(amount) for token, amount in loan.debt.values.items()}
                    for loan in loan_entities_values
                ],
            }
        )

        return result_df

    def run(self) -> None:
        """
        Runs the loan state computation for the zkLend protocol.
        """
        for protocol_address in self.PROTOCOL_ADDRESSES:
            # while True:
            data = self.get_data(protocol_address, self.last_block)
            if not data:
                self.last_block += self.PAGINATION_SIZE
                continue
            # if not data:
            #     break
            processed_data = self.process_data(data)
            self.save_data(processed_data)
            self.last_block += self.PAGINATION_SIZE
            logger.info(f"Processed data up to block {self.last_block}")


def run_loan_states_computation_for_zklend() -> None:
    """
    Runs the zkLend loan state computation.
    """
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting zkLend loan state computation")
    computation = ZkLendLoanStateComputation()
    computation.run()

    logger.info("Finished zkLend loan state computation, Time taken: %s seconds", monotonic() - start)
