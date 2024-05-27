import logging

import pandas as pd
from time import monotonic
from handlers.loan_states.abstractions import LoanStateComputationBase
from handlers.loan_states.hashtack_v1.events import HashstackV1State
from tools.constants import ProtocolAddresses, ProtocolIDs

logger = logging.getLogger(__name__)


class HashtackV1StateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the HashtackV1 protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.HASHSTACK_V1
    PROTOCOL_ADDRESSES = ProtocolAddresses().HASHSTACK_V1_R_TOKENS | ProtocolAddresses().HASHSTACK_V1_D_TOKENS

    def process_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Processes the data retrieved from the DeRisk API.
        This method must be implemented by subclasses to define the data processing steps.

        :param data: The data retrieved from the DeRisk API.
        :type data: list[dict]

        :return: pd.DataFrame
        """
        hashtack_v1_state = HashstackV1State()
        events_mapping = hashtack_v1_state.EVENTS_METHODS_MAPPING
        # Init DataFrame
        df = pd.DataFrame(data)
        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]
        for index, row in df_filtered.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(hashtack_v1_state, method_name, row)

        result_df = self.get_result_df(hashtack_v1_state.loan_entities)
        return result_df


def run_loan_states_computation_for_hashstack_v1() -> None:
    """
    Runs the Hashstack loan state computation.
    """
    start = monotonic()
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting Hashstack v1 loan state computation")
    computation = HashtackV1StateComputation()
    computation.run()

    logger.info(
        "Finished Hashstack v1 loan state computation, Time taken: %s seconds",
        monotonic() - start,
    )


if __name__ == "__main__":
    run_loan_states_computation_for_hashstack_v1()