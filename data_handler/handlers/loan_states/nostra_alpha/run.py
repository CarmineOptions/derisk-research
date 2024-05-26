import logging

import pandas as pd
from time import monotonic
from handlers.loan_states.abstractions import LoanStateComputationBase
from handlers.loan_states.nostra_alpha.events import NostraAlphaState
from tools.constants import ProtocolAddresses, ProtocolIDs

logger = logging.getLogger(__name__)


class NostraAlphaStateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the NOSTRA_ALPHA protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.NOSTRA_ALPHA.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().NOSTRA_ALPHA_ADDRESSES

    def process_data(self, data: list[dict]) -> pd.DataFrame:
        """
        Processes the data retrieved from the DeRisk API.
        This method must be implemented by subclasses to define the data processing steps.

        :param data: The data retrieved from the DeRisk API.
        :type data: list[dict]

        :return: pd.DataFrame
        """
        nostra_alpha_state = NostraAlphaState()
        events_mapping = nostra_alpha_state.EVENTS_METHODS_MAPPING
        # Init DataFrame
        df = pd.DataFrame(data)
        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]
        for index, row in df_filtered.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(nostra_alpha_state, method_name, row)

        result_df = self.get_result_df(nostra_alpha_state.loan_entities)
        return result_df


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
