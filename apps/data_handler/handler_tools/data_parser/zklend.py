"""
This module contains the logic to parse the zkLend data to human-readable format.
"""

from typing import Any, List
from data_handler.handler_tools.data_parser.serializers import (
    AccumulatorsSyncEventData,
    LiquidationEventData,
    WithdrawalEventData,
    BorrowingEventData,
    RepaymentEventData,
    DepositEventData,
    CollateralEnabledDisabledEventData,
)


class ZklendDataParser:
    """
    Parses the zkLend data to human-readable format.
    """

    @classmethod
    def parse_accumulators_sync_event(
        cls, event_data: list[Any]
    ) -> AccumulatorsSyncEventData:
        """
        Parses the AccumulatorsSync event data into a human-readable format using the AccumulatorsSyncEventData serializer.

        Args:
            event_data (list[Any]): A list containing the raw event data, typically with 3 elements:
                token, lending accumulator, and debt accumulator.

        Returns:
            AccumulatorsSyncEventData: A model with the parsed event data.
        """
        return AccumulatorsSyncEventData(
            token=event_data[0],
            lending_accumulator=event_data[1],
            debt_accumulator=event_data[2],
        )

    @classmethod
    def parse_deposit_event(cls, event_data: List[Any]) -> DepositEventData:
        """
        Convert the event list to a Deposit event data object
        :param event_data: list of length 4 of the event data
        :return: DepositEventData
        """
        return DepositEventData(
            user=event_data[0],
            token=event_data[1],
            face_amount=event_data[2],
        )

    @classmethod
    def parse_withdrawal_event(cls, event_data: list[Any]) -> WithdrawalEventData:
        """
        Parses the Withdrawal event data into a human-readable format using the WithdrawalEventData serializer.

        The event data is fetched from on-chain logs and is structured in the following way:
        - event_data[0]: The user address (as a hexadecimal string).
        - event_data[1]: The amount withdrawn (as a string).
        - event_data[2]: The token address (as a hexadecimal string).
        - event_data[3]: Additional data, if applicable (e.g., transaction ID).

        Args:
            event_data (list[Any]): A list containing the raw event data, typically with 3 or more elements:
                user address, amount withdrawn, token address, and additional data.

        Returns:
            WithdrawalEventData: A Pydantic model with the parsed and validated event data in a human-readable format.
        """
        return WithdrawalEventData(
            user=event_data[0],
            amount=event_data[1],
            token=event_data[2],
        )

    @classmethod
    def parse_borrowing_event(cls, event_data: list[Any]) -> BorrowingEventData:
        """
        Parses the Borrowing event data.

        Args:
            event_data (list[Any]): A list containing the raw event data, typically with 4 elements.

        Returns:
            BorrowingEventData: A model with the parsed event data.
        """
        return BorrowingEventData(
            user=event_data[0],
            token=event_data[1],
            raw_amount=event_data[2],
            face_amount=event_data[3],
        )

    @classmethod
    def parse_repayment_event(cls, event_data: List[Any]) -> RepaymentEventData:
        """
        Parses the Repayment event data into a human-readable format using the RepaymentEventData serializer.

        Args:
            event_data (List[Any]): A list containing the raw repayment event data, typically with 5 elements.

        Returns:
            RepaymentEventData: A model with the parsed event data.
        """
        return RepaymentEventData(
            repayer=event_data[0],
            beneficiary=event_data[1],
            token=event_data[2],
            raw_amount=event_data[3],
            face_amount=event_data[4],
        )

    @classmethod
    def parse_liquidation_event(cls, event_data: list[Any]) -> LiquidationEventData:
        """
        Parses the Liquidation event data.

        Args:
            event_data (list[Any]): A list containing the raw liquidation event data, typically with 7 elements.

        Returns:
            LiquidationEventData: A model with the parsed event data.
        """
        return LiquidationEventData(
            liquidator=event_data[0],
            user=event_data[1],
            debt_token=event_data[2],
            debt_raw_amount=event_data[3],
            debt_face_amount=event_data[4],
            collateral_token=event_data[5],
            collateral_amount=event_data[6],
        )

    @classmethod
    def parse_collateral_enabled_disabled_event(
        cls, event_data: dict[str, list[str]]
    ) -> CollateralEnabledDisabledEventData:
        """
        Parses the Collateral enabled/disabled event data.

        Args:
            event_data (Dict[str, List[str]]): A dictionary where the keys are field names and values are lists
                                               containing the corresponding data as strings.:

        Returns:
            CollateralEnabledDisabledEventData: A model with the parsed event data.
        """
        return CollateralEnabledDisabledEventData(
            user=event_data["data"][0],
            token=event_data["data"][1],
        )