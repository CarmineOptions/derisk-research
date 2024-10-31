""" Module for calculating interest rates on the Hashstack V0 protocol. """
import asyncio
import logging
from decimal import Decimal

from data_handler.handler_tools.api_connector import DeRiskAPIConnector
from data_handler.handler_tools.constants import TOKEN_MAPPING
from data_handler.handlers.blockchain_call import NET
from data_handler.handlers.helpers import InterestRateState

from data_handler.db.crud import DBConnector
from data_handler.db.models import InterestRate
from shared.constants import ProtocolIDs

HASHSTACK_INTEREST_RATE_ADDRESS = (
    "0x01b862c518939339b950d0d21a3d4cc8ead102d6270850ac8544636e558fab68"
)

HASHSTACK_ID = ProtocolIDs.HASHSTACK_V0.value

SECONDS_IN_YEAR = Decimal(365 * 24 * 60 * 60)


class HashstackV0InterestRate:
    """Class for calculating interest rates on the Hashstack V0 protocol."""

    PAGINATION_SIZE = 1000
    DEFAULT_START_BLOCK = 0

    def __init__(self):
        """
        Initialize the HashstackV0InterestRate object.
        """
        self.api_connector = DeRiskAPIConnector()
        self.db_connector = DBConnector()
        self.last_block_data: InterestRate | None = (
            self.db_connector.get_last_interest_rate_record_by_protocol_id(HASHSTACK_ID)
        )
        self.events: list[dict] = []
        self.blocks_data: list[InterestRate] = []
        self._events_over: bool = False

    def _set_events(self, start_block: int, end_block: int) -> None:
        """
        Fetch events from the API, filter them by token and set them to the events attribute.
        Set flag that events are over if the result is an error.
        """
        if not isinstance(start_block, int) or not isinstance(end_block, int):
            logging.info("Invalid block numbers provided.")
            self.events.clear()
        self.events.clear()
        result = self.api_connector.get_data(
            HASHSTACK_INTEREST_RATE_ADDRESS,
            start_block,
            end_block,
        )
        if isinstance(result, dict):
            logging.info(f"Error while fetching events: {result.get('error', 'Unknown error')}")
            self.events = []
            self._events_over = True
            return
        self.events = result

    def _add_interest_rate_entry(self, interest_rate_entry: InterestRate) -> None:
        """
        Add the interest rate entry to the blocks data and update last block data stored.
        :param interest_rate_entry: InterestRate - interest rate entry to add.
        """
        self.blocks_data.append(interest_rate_entry)
        self.last_block_data = interest_rate_entry

    def calculate_interest_rates(self) -> None:
        """
        Calculate the interest rates for provided events range.
        :return: list[InterestRate] - list of blocks with interest rates data.
        """
        if not self.events:
            return
        percents_decimals_shift = Decimal("0.0001")
        interest_rate_state = InterestRateState(
            self.events[0]["block_number"], self.last_block_data
        )

        for event in self.events:
            # If block number in event is different from previous, add block data
            if interest_rate_state.current_block != event["block_number"]:
                self._add_interest_rate_entry(
                    interest_rate_state.build_interest_rate_model(HASHSTACK_ID)
                )

            # Get token name. Validate event `key_name` and token name.
            token_name = TOKEN_MAPPING.get(event["data"][0], "")
            interest_rate_state.current_block = event["block_number"]
            interest_rate_state.current_timestamp = event["timestamp"]
            if not token_name or event["key_name"] != "current_apr":
                continue

            # Set initial timestamp values for the first token event
            if (not self.last_block_data
                    or interest_rate_state.previous_token_timestamps[token_name] == 0):
                interest_rate_state.previous_token_timestamps[token_name] = event["timestamp"]
                continue

            # Get needed variables
            seconds_passed = interest_rate_state.get_seconds_passed(token_name)
            borrow_apr_bps = Decimal(int(event["data"][1], 16))
            supply_apr_bps = Decimal(int(event["data"][2], 16))

            # Calculate interest rate for supply and borrow and convert to percents using the formula:
            # (apr * seconds_passed / seconds_in_year) / 10000
            cumulative_collateral_interest_rate_increase = (
                supply_apr_bps * seconds_passed / SECONDS_IN_YEAR
            ) * percents_decimals_shift
            cumulative_debt_interest_rate_increase = (
                borrow_apr_bps * seconds_passed / SECONDS_IN_YEAR
            ) * percents_decimals_shift
            interest_rate_state.update_state_cumulative_data(
                token_name,
                event["block_number"],
                cumulative_collateral_interest_rate_increase,
                cumulative_debt_interest_rate_increase,
            )

        # Write last block data
        self._add_interest_rate_entry(interest_rate_state.build_interest_rate_model(HASHSTACK_ID))

    async def _run_async(self) -> None:
        """Asynchronous function for running the interest rate calculation process and fetching data from on-chain."""
        latest_block = await NET.get_block_number()
        previous_block = (
            self.last_block_data.block if self.last_block_data else self.DEFAULT_START_BLOCK
        )
        if previous_block == latest_block:
            return
        start_block, end_block = previous_block, min(
            previous_block + self.PAGINATION_SIZE, latest_block
        )
        # Fetch and set events until blocks are over
        while start_block < latest_block and not self._events_over:
            self._set_events(start_block, end_block)
            start_block += self.PAGINATION_SIZE
            end_block = min(start_block + self.PAGINATION_SIZE, latest_block)
            if not self.events:
                continue
            self.calculate_interest_rates()
            self._write_to_db()

    def _write_to_db(self) -> None:
        """Write the calculated interest rates to the database and clear blocks data."""
        self.db_connector.write_batch_to_db(self.blocks_data)
        self.blocks_data.clear()

    def run(self) -> None:
        """Run the interest rate calculation process from the last stored block or from 0 block."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(self._run_async())
            asyncio.set_event_loop(loop)
        else:
            loop.run_until_complete(self._run_async())


if __name__ == "__main__":
    interest_rate = HashstackV0InterestRate()
    interest_rate.run()
