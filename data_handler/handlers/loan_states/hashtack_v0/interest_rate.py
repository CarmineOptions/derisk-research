from handler_tools.api_connector import DeRiskAPIConnector
from handlers.loan_states.hashtack_v0.events import HashstackV0Event

from decimal import Decimal


HASHSTACK_ADDRESS = "0x01b862c518939339b950d0d21a3d4cc8ead102d6270850ac8544636e558fab68"

SECONDS_IN_YEAR = Decimal(365 * 24 * 60 * 60)


class HashstackV0InterestRate:
    """Class for calculating interest rates for a given token on the Hashstack V0 protocol."""
    def __init__(self, token: str, min_block_number: int, max_block_number: int):
        """
        Initialize the HashstackV0InterestRate object.
        :param token: str - The token address in hexadecimal.
        :param min_block_number: int - The lower block number from which to retrieve events.
        :param max_block_number: int - The upper block number to which to retrieve events.
        """
        self.token = token
        self.min_block_number = min_block_number
        self.max_block_number = max_block_number
        self.interest_rates = []
        self.api_connector = DeRiskAPIConnector()
        self.events = None
        self._set_events()

    def _set_events(self):
        """Fetch events from the API, filter them by token and set them to the events attribute."""
        if not isinstance(self.min_block_number, int) or not isinstance(self.max_block_number, int):
            raise ValueError("Block numbers must be integers")
        result = self.api_connector.get_data(HASHSTACK_ADDRESS, self.min_block_number, self.max_block_number)
        # token_address = hex(int(self.token, base=16))
        if isinstance(result, dict):
            raise RuntimeError(f"Error while fetching events: {result.get('error', 'Unknown error')}")
        self.events = list(filter(lambda event: event["data"][0] == self.token, result))

    def calculate_interest_rate(self):
        if not self.events:
            return
        supply_interest_rate_cum = Decimal("0")
        borrow_interest_rate_cum = Decimal("0")
        percents_decimals_shift = Decimal(10000)
        for index, event in enumerate(self.events):
            # First block will have 0 interest rate
            if index == 0:
                first_event = HashstackV0Event(
                    event["block_number"], event["timestamp"], supply_interest_rate_cum, borrow_interest_rate_cum
                )
                self.interest_rates.append(first_event)
                continue

            # Get needed variables
            current_timestamp = event["timestamp"]
            seconds_passed = Decimal(current_timestamp - self.events[index - 1]["timestamp"])
            borrow_apr = Decimal(int(event["data"][1], 16))
            supply_apr = Decimal(int(event["data"][2], 16))

            # Calculate interest rate for supply and borrow and convert to percents using the formula:
            # (apr * seconds_passed / seconds_in_year) / 10000
            supply_interest_rate_cum += (supply_apr * seconds_passed / SECONDS_IN_YEAR) / percents_decimals_shift
            borrow_interest_rate_cum += (borrow_apr * seconds_passed / SECONDS_IN_YEAR) / percents_decimals_shift
            current_event = HashstackV0Event(
                event["block_number"], current_timestamp, supply_interest_rate_cum, borrow_interest_rate_cum
            )
            self.interest_rates.append(current_event)

    def serialize(self):
        """Get interests rates serialized as database models."""
        # TODO: Add integration with existing sqlalchemy model
        return [event.serialize() for event in self.interest_rates]


if __name__ == '__main__':
    interest_rate = HashstackV0InterestRate("0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d", 646000, 647000)
    interest_rate.calculate_interest_rate()
    print(interest_rate.serialize())
