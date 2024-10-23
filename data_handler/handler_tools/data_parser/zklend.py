from decimal import Decimal

from serializers import AccumulatorsSyncEvent


class ZklendDataParser:
    """
    Parses the zkLend data to human-readable format.
    """

    @classmethod
    def parse_accumulators_sync_event(cls, event_data):
        parsed_event = AccumulatorsSyncEvent(
            token=event_data[0],
            lending_accumulator=Decimal(int(event_data[1], 16)) / Decimal("1e27"),
            debt_accumulator=Decimal(int(event_data[2], 16)) / Decimal("1e27"),
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
        # TODO: Implement parsing logic for Liquidation event
        pass
