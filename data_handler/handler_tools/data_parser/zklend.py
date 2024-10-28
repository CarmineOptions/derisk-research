from typing import Any

from data_handler.handler_tools.data_parser.serializers import (
    AccumulatorsSyncEventData,
    EventAccumulatorsSyncData,
    LiquidationEventData,
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
        Parses the AccumulatorsSync event data into a human-readable format using the AccumulatorsSyncEvent serializer.

        The event data is fetched from on-chain logs and is structured in the following way:
        - event_data[0]: The token address (as a hexadecimal string).
        - event_data[1]: Lending accumulator value (as a hexadecimal string).
        - event_data[2]: Debt accumulator value (as a hexadecimal string).

        Example of raw event data can be found on Starkscan:
        https://starkscan.co/event/0x029628b89875a98c1c64ae206e7eb65669cb478a24449f3485f5e98aba6204dc_0

        Args:
            event_data (list[Any]): A list containing the raw event data, typically with 3 elements:
                token, lending accumulator (hexadecimal string), and debt accumulator (hexadecimal string).

        Returns:
            AccumulatorsSyncEvent: A Pydantic model with the parsed and validated event data in a human-readable format.
        """
        data = EventAccumulatorsSyncData.from_raw_data(event_data)
        parsed_event = AccumulatorsSyncEventData(
            token=data.token,
            lending_accumulator=data.lending_accumulator,
            debt_accumulator=data.debt_accumulator,
        )
        return parsed_event

    @classmethod
    def parse_deposit_event(cls, event_data):
        # TODO: Implement parsing logic for Deposit event
        pass

    @classmethod
    def parse_collateral_enabled_disabled_event(cls, event_data):
        # TODO: Implement parsing logic for CollateralEnabled event
        # TODO put it together with disabled event
        pass

    @classmethod
    def parse_withdrawal_event(cls, event_data):
        # TODO: Implement parsing logic for Withdrawal event
        pass

    @classmethod
    def parse_borrowing_event(cls, event_data):
        # TODO: Implement parsing logic for Borrowing event
        pass

    @classmethod
    def parse_repayment_event(cls, event_data):
        # TODO: Implement parsing logic for Repayment event
        pass

    @classmethod
    def parse_liquidation_event(cls, event_data):
        """
        Convert the event list to a Liquidation event data object

        :event_data - List of length 7 of the event data

        Returns
        LiquidationEventData
        """
        event_data = LiquidationEventData(
            liquidator=event_data[0],
            user=event_data[1],
            debt_token=event_data[2],
            debt_raw_amount=event_data[3],
            debt_face_amount=event_data[4],
            collateral_token=event_data[5],
            collateral_amount=event_data[6],
        )
        return event_data
