import logging
import pandas as pd
from db.crud import InitializerDBConnector
from db.models import HashtackCollateralDebt
from decimal import Decimal
from handlers.loan_states.hashtack_v0.events import HashstackV0LoanEntity


logger = logging.getLogger(__name__)


class HashtackV0Initializer:
    """
    A class that initializes the HashstackV0 loan states.
    """

    def __init__(self, hashtack_state: "HashstackV0State"):
        self.db_connector = InitializerDBConnector()
        self.hashtack_state = hashtack_state

    def set_last_loan_states_per_loan_ids(self, users_ids: list[str]) -> None:
        """
        Sets the last loan states for the given users.

        :param users_ids: The list of user ids to set the loan states for.
        """
        loan_states = self.db_connector.get_hashtackv0_by_loan_ids(users_ids)
        for loan_state in loan_states:
            self._set_loan_state_per_loan_id(loan_state)

    @staticmethod
    def get_loan_ids(df: pd.DataFrame) -> list:
        """
        Get the unique loan ids from the given DataFrame.

        :param df: The DataFrame to get the loan ids from.
        :return: The list of unique loan ids.
        """
        key_mapping = {
            "new_loan": 0,
            "collateral_added": 9,
            "collateral_withdrawal": 9,
            "loan_withdrawal": 0,
            "loan_repaid": 0,
            "loan_swap": 0,
            "loan_interest_deducted": 11,
            "liquidated": 0,
        }

        loan_ids = []

        for index, event in df.iterrows():
            method_name = event["key_name"]
            if method_name in key_mapping:
                try:
                    loan_id_index = key_mapping[method_name]
                    loan_id = int(event["data"][loan_id_index], base=16)
                    loan_ids.append(loan_id)
                except (IndexError, ValueError, KeyError):
                    logger.info(f"Failed to get loan id from event: {event}")
                    continue

        return list(set(loan_ids))

    def _set_loan_state_per_loan_id(self, loan_state: HashtackCollateralDebt) -> None:
        """
        Sets the loan state for a user.

        :param loan_state: The loan state data.
        """
        self.hashtack_state.loan_entities[loan_state.loan_id] = HashstackV0LoanEntity(
            user=loan_state.user_id, debt_category=loan_state.debt_category
        )
        user_loan_state = self.hashtack_state.loan_entities[loan_state.loan_id]
        user_loan_state.debt_category = loan_state.debt_category
        user_loan_state.original_collateral.values = self._convert_float_to_decimal(
            loan_state.original_collateral
        )
        user_loan_state.borrowed_collateral.values = self._convert_float_to_decimal(
            loan_state.borrowed_collateral
        )
        user_loan_state.collateral.values = self._convert_float_to_decimal(
            loan_state.collateral
        )
        user_loan_state.debt.values = self._convert_float_to_decimal(loan_state.debt)

        # extra field to avoid saving to db
        user_loan_state.has_skip = True

    @staticmethod
    def _convert_float_to_decimal(data: dict | None) -> dict | None:
        """
        Convert float values to Decimal for a given dictionary.
        :param data: The dictionary to convert.
        :return: The converted dictionary or None
        """
        if data:
            return {k: Decimal(v) for k, v in data.items()}

        return None
