import logging

import pandas as pd
from time import monotonic
from handlers.loan_states.abstractions import LoanStateComputationBase
from handlers.loan_states.zklend.events import ZkLendState
from tools.constants import ProtocolAddresses, ProtocolIDs

logger = logging.getLogger(__name__)


class ZkLendLoanStateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the zkLend protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.ZKLEND.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().ZKLEND_MARKET_ADDRESSES

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
        try:
            df = pd.DataFrame(data)
        except ValueError:
            logger.error("No data to process")
            return pd.DataFrame()

        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]
        for index, row in df_filtered.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(zklend_state, method_name, row)

        result_df = self.get_result_df(zklend_state.loan_entities)
        return result_df


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
