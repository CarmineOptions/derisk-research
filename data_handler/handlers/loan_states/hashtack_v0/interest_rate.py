import logging
from decimal import Decimal

from db.crud import DBConnector
from db.models import InterestRate
from handler_tools.api_connector import DeRiskAPIConnector
from handler_tools.constants import ProtocolIDs, TOKEN_MAPPING
from handlers.loan_states.hashtack_v0.events import HashstackV0Event

HASHSTACK_INTEREST_RATE_ADDRESS = "0x01b862c518939339b950d0d21a3d4cc8ead102d6270850ac8544636e558fab68"

HASHSTACK_ID = ProtocolIDs.HASHSTACK_V0.value

SECONDS_IN_YEAR = Decimal(365 * 24 * 60 * 60)


class HashstackV0InterestRate:
    """Class for calculating interest rates on the Hashstack V0 protocol."""

    PAGINATION_SIZE = 1000

    def __init__(self):
        """
        Initialize the HashstackV0InterestRate object.
        """
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = DBConnector()
        self.last_block_data: InterestRate | None = self.db_connector.get_last_interest_rate_record_by_protocol_id(
            HASHSTACK_ID
        )
        self.events: list = []

    def _set_events(self, start_block: int = 0):
        """Fetch events from the API, filter them by token and set them to the events attribute."""
        self.events.clear()
        result = self.api_connector.get_data(
            HASHSTACK_INTEREST_RATE_ADDRESS,
            start_block,
            start_block + self.PAGINATION_SIZE,
        )
        if isinstance(result, dict):
            logging.info(f"Error while fetching events: {result.get('error', 'Unknown error')}")
            self.events = []
            return
        self.events = result

    def serialize_interest_rates(self, collateral_data, debt_data):
        collateral = {
            token_name: float(value) for token_name, value in collateral_data.items()
        }
        debt = {
            token_name: float(value) for token_name, value in debt_data.items()
        }
        return {"collateral": collateral, "debt": debt}

    def deserialize_interest_rates(self):
        if not self.last_block_data:
            return {}, {}
        collateral = {
            token_name: Decimal(value) for token_name, value in self.last_block_data.collateral.items()
        }
        debt = {
            token_name: Decimal(value) for token_name, value in self.last_block_data.debt.items()
        }
        return collateral, debt

    def calculate_interest_rates(self) -> list[InterestRate]:
        """Calculate the interest rates for the given token."""
        if not self.events:
            return []
        percents_decimals_shift = Decimal("0.0001")
        blocks_data: list[InterestRate] = []
        if self.last_block_data:
            cumulative_collateral, cumulative_debt = self.deserialize_interest_rates()
            # cumulative_collateral = self.last_block_data.collateral
            # cumulative_debt = self.last_block_data.debt
        else:
            cumulative_collateral = {
                token_name: Decimal("1") for token_name in TOKEN_MAPPING.values()
            }
            cumulative_debt = cumulative_collateral.copy()
        if self.last_block_data:
            token_timestamps = {
                token_name: self.last_block_data.timestamp for token_name in TOKEN_MAPPING.values()
            }
        else:
            token_timestamps = {
                token_name: 0 for token_name in TOKEN_MAPPING.values()
            }
        current_block = self.events[0]["block_number"]
        latest_timestamp = 0
        for index, event in enumerate(self.events):
            # First block will have 0 interest rate
            if current_block != event["block_number"]:
                interest_rate_entry = InterestRate(
                        block=current_block, timestamp=latest_timestamp, protocol_id=HASHSTACK_ID,
                        **self.serialize_interest_rates(cumulative_collateral, cumulative_debt)
                    )
                blocks_data.append(
                    interest_rate_entry
                )
                self.last_block_data = interest_rate_entry
            token_name = TOKEN_MAPPING.get(event["data"][0], "")
            if not token_name or event["key_name"] != "current_apr":
                continue
            if not self.last_block_data and token_timestamps[token_name] == 0:
                token_timestamps[token_name] = event["timestamp"]
                latest_timestamp = event["timestamp"]
                continue

            # Get needed variables
            current_timestamp = event["timestamp"]
            seconds_passed = Decimal(current_timestamp - token_timestamps[token_name])
            borrow_apr_bps = Decimal(int(event["data"][1], 16))
            supply_apr_bps = Decimal(int(event["data"][2], 16))

            # Calculate interest rate for supply and borrow and convert to percents using the formula:
            # (apr * seconds_passed / seconds_in_year) / 10000
            current_collateral_change = (supply_apr_bps * seconds_passed / SECONDS_IN_YEAR) * percents_decimals_shift
            cumulative_collateral[token_name] += current_collateral_change
            current_debt_change = (borrow_apr_bps * seconds_passed / SECONDS_IN_YEAR) * percents_decimals_shift
            cumulative_debt[token_name] += current_debt_change
            latest_timestamp = current_timestamp
            current_block = event["block_number"]
        return blocks_data

    def run(self) -> None:
        start_block = self.last_block_data.block if self.last_block_data else 273178

        retries = 0
        # if not self.events:
        #     return

        while self.events or retries < 5:
            self._set_events(start_block)
            if start_block > 293178:
                # TODO: Remove this condition
                return
            if not self.events:
                retries += 1
                start_block += self.PAGINATION_SIZE
                self._set_events(start_block)
                continue
            retries = 0
            processed_data = self.calculate_interest_rates()
            self.db_connector.write_batch_to_db(processed_data)
            start_block += self.PAGINATION_SIZE

    def write_data(self, interest_rate_data: list[InterestRate]):
        pass


if __name__ == "__main__":
    interest_rate = HashstackV0InterestRate(
        # "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    )
    interest_rate.run()
    # interest_rate.calculate_interest_rates()
    # print(interest_rate.serialize())

