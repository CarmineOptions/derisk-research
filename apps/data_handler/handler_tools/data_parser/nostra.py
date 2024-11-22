from data_handler.handler_tools.data_parser.serializers import (
    DebtMintEventData,
    DebtBurnEventData
)


class NostraDataParser:
    """
    Parses the nostra data to human-readable format.
    """
    def parse_interest_rate_model_event(self):
        pass

    def parse_non_interest_bearing_collateral_mint_event(self):
        pass

    def parse_non_interest_bearing_collateral_burn_event(self):
        pass

    def parse_interest_bearing_collateral_mint_event(self):
        pass

    def parse_interest_bearing_collateral_burn_event(self):
        pass

    def parse_debt_transfer_event(self):
        pass

    def parse_debt_mint_event(self, event_data: list[Any]) -> DebtMintEventData:
        return DebtMintEventData(
            user=event_data[0],
            token=event_data[1]
        )

    def parse_debt_burn_event(self, event_data: list[Any]) -> DebtBurnEventData:
        return DebtBurnEventData(
            user=event_data[0],
            amount=event_data[1]
        )