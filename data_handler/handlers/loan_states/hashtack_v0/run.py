import logging

import pandas as pd
from time import monotonic
from handlers.loan_states.abstractions import LoanStateComputationBase
from handlers.loan_states.hashtack_v0.events import HashstackV0State, LoanEntity
from handler_tools.constants import ProtocolAddresses, ProtocolIDs
from handlers.loan_states.hashtack_v0.utils import HashtackV0Initializer

logger = logging.getLogger(__name__)


class HashtackV0StateComputation(LoanStateComputationBase):
    """
    A class that computes the loan states for the HashstackV0 protocol.
    """

    PROTOCOL_TYPE = ProtocolIDs.HASHSTACK_V0.value
    PROTOCOL_ADDRESSES = ProtocolAddresses().HASHSTACK_V0_ADDRESSES

    def process_interest_rate_event(
        self, instance_state: "State", event: pd.Series
    ) -> None:
        """
        Processes the interest rate event.

        :param instance_state: The instance of the state class to call the method on.
        :type instance_state: object
        :param event: The event data as a pandas Series.
        """
        pass

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

        # init HashtackV0Initializer
        hashtack_initializer = HashtackV0Initializer(hashtack_v0_state)
        loan_ids = hashtack_initializer.get_loan_ids(df)
        hashtack_initializer.set_last_loan_states_per_loan_ids(list(set(loan_ids)))

        # Filter out events that are not in the mapping
        df_filtered = df[df["key_name"].isin(events_mapping.keys())]

        for index, row in df_filtered.iterrows():
            method_name = events_mapping.get(row["key_name"], "") or ""
            self.process_event(hashtack_v0_state, method_name, row)

        result_df = self.get_result_df(hashtack_v0_state.loan_entities)
        return result_df

    def get_result_df(self, loan_entities: dict) -> pd.DataFrame:
        """
        Creates a DataFrame with the loan state based on the loan entities.
        :param loan_entities: dictionary of loan entities
        :return: dataframe with loan state
        """

        filtered_loan_entities: dict = {}
        # remove objects from loan_entities_values if the object has `has_skip` attribute
        for loan_id, loan_entity in loan_entities.items():
            has_skip = getattr(loan_entity, "has_skip", None)
            if not has_skip:
                filtered_loan_entities[loan_id] = loan_entity

        # if there are no loan entities, return an empty DataFrame
        if not loan_entities:
            return pd.DataFrame()
        result_dict = {
            "protocol": [self.PROTOCOL_TYPE for _ in filtered_loan_entities.keys()],
            "user": [
                loan_entity.user for loan_entity in filtered_loan_entities.values()
            ],
            "collateral": [
                {
                    token: float(amount)
                    for token, amount in loan.collateral.values.items()
                }
                for loan in filtered_loan_entities.values()
            ],
            "block": [
                entity.extra_info.block for entity in filtered_loan_entities.values()
            ],
            "timestamp": [
                entity.extra_info.timestamp
                for entity in filtered_loan_entities.values()
            ],
            "debt": [
                {token: float(amount) for token, amount in loan.debt.values.items()}
                for loan in filtered_loan_entities.values()
            ],
        }

        result_df = pd.DataFrame(result_dict)
        return result_df

    def run(self) -> None:
        """
        Runs the loan state computation for the specific protocol.
        """
        max_retries = 10000 # FIXME change it after first run on the server
        retry = 0
        self.last_block = 21000 # FIXME change it after first run on the server

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
