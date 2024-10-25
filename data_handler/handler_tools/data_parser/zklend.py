from serializers import LiquidationEventData


class ZklendDataParser:
    """
    Parses the zkLend data to human-readable format.
    """

    @classmethod
    def parse_accumulators_sync_event(cls, event_data):
        # TODO: Implement parsing logic for AccumulatorsSync event
        pass

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
