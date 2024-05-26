import asyncio
from decimal import Decimal
from functools import partial
from itertools import zip_longest

from src.blockchain_call import func_call
from web_app.order_books.abstractions import OrderBookBase
from web_app.order_books.haiko.api_connector import (
    HaikoAPIConnector,
    HaikoBlastAPIConnector,
)
from web_app.order_books.haiko.logger import get_logger

HAIKO_MARKET_MANAGER_ADDRESS = ("0x0038925b0bcf4dce081042ca26a96300d9e181b910328db54a6c89e5451503f5")
HAIKO_MAX_TICK = 7906205


class HaikoOrderBook(OrderBookBase):
    DEX = "Haiko"

    def __init__(self, token_a, token_b):
        super().__init__(token_a, token_b)
        self.current_price = Decimal("0")
        self.haiko_connector = HaikoAPIConnector()
        self.blast_connector = HaikoBlastAPIConnector()
        self.logger = get_logger("./logs", echo=True)
        self._check_tokens_supported()

    def _check_tokens_supported(self) -> None:
        """Check if a pair of tokens is supported by Haiko"""
        supported_tokens = self.haiko_connector.get_supported_tokens()
        if isinstance(supported_tokens, dict) and supported_tokens.get("error"):
            raise RuntimeError(f"Unexpected error from API: {supported_tokens}")
        supported_tokens_filtered = [
            token
            for token in supported_tokens
            if token["address"] in (self.token_a, self.token_b)
        ]
        if len(supported_tokens_filtered) != 2:
            raise ValueError("One of tokens isn't supported by Haiko")

    def _filter_markets_data(self, all_markets_data: list) -> list:
        """
        Filter markets for actual token pair.
        :param all_markets_data: all supported markets provided bt Haiko
        :return: list of markets data for actual token pair
        """
        return list(
            filter(
                lambda market: market["baseToken"]["address"] == self.token_a
                and market["quoteToken"]["address"] == self.token_b,
                all_markets_data,
            )
        )

    async def get_market_ticks_liquidity(self, market_id) -> list:
        """
        Get information about ticks from market manager contract.
        :param market_id: ID of the market for which ticks will be fetched.
        :return list of ticks in form: [count of ticks, tick1, price1, sign1, liquidity_delta1, sign_delta1, tick2...]
        """
        try:
            ticks_info = await func_call(HAIKO_MARKET_MANAGER_ADDRESS, "depth", [market_id])
            items_in_group = (len(ticks_info) - 1) // ticks_info[0]
            return self.group_ticks_info(ticks_info[1:], items_in_group)
        except Exception as e:
            self.logger.critical(f"Pair of tokens: {self.token_a}-{self.token_b}")
            self.logger.critical(f"Failed to get ticks for market: {market_id}")
            self.logger.critical(f"Error: {e}\n")
            return []

    def set_current_price(self, current_tick: Decimal) -> None:
        """
        Set the current price based on the current tick.
        :param current_tick: Int - Current tick
        """
        self.tick_current_price = self.tick_to_price(current_tick)

    def sort_asks_bids(self):
        """Sort bids and asks data in correct order."""
        self.asks.sort(key=lambda ask: ask[0])
        self.bids.sort(key=lambda bid: bid[0], reverse=True)

    async def fetch_price_and_liquidity(self) -> None:
        all_markets_data = self.haiko_connector.get_token_markets()
        if isinstance(all_markets_data, dict) and all_markets_data.get("error"):
            raise RuntimeError(f"Unexpected error from Haiko API: {all_markets_data}")

        tokens_markets = self._filter_markets_data(all_markets_data)
        latest_block_info = self.blast_connector.get_block_info()
        if latest_block_info.get("error"):
            raise RuntimeError(f"Blast-api returned an error: {latest_block_info}")

        self.block = latest_block_info["result"]["block_number"]
        self.timestamp = latest_block_info["result"]["timestamp"]

        if not tokens_markets:
            message = "Markets for this pair isn't available for now"
            self.logger.critical(f"Pair of tokens: {self.token_a}-{self.token_b}")
            self.logger.critical(f"{message}\n")
            return

        for market in tokens_markets:
            market_id = market["marketId"]
            liquidity = await func_call(HAIKO_MARKET_MANAGER_ADDRESS, "liquidity", [market_id])
            if not liquidity:
                continue
            liquidity = Decimal(liquidity[0])
            market_ticks_liquidity = await self.get_market_ticks_liquidity(market_id)
            if not market_ticks_liquidity or market_ticks_liquidity[0] == 0:
                continue
            self._calculate_order_book(market_ticks_liquidity, liquidity, market["currLimit"])

        self.sort_asks_bids()

        self.current_price = max(tokens_markets, key=lambda x: Decimal(x["tvl"]))["currPrice"]

    def _calculate_order_book(
        self, market_ticks_liquidity: list, liquidity: Decimal, current_tick: Decimal
    ) -> None:
        self.set_current_price(current_tick)
        min_price, max_price = self.calculate_price_range()
        process_ticks = partial(self.process_ticks, liquidity, min_price, max_price)
        asks, bids = self.divide_ticks_on_bids_asks(market_ticks_liquidity)
        process_ticks(asks, is_ask=True)
        process_ticks(bids, is_ask=False)

    def process_ticks(
        self,
        market_liquidity: Decimal,
        min_price: Decimal,
        max_price: Decimal,
        ticks: tuple,
        is_ask=True,
    ) -> None:
        """
        Process ticks and add info about price and liquidity to correct list.
        :param market_liquidity: liquidity defined in market pool
        :param min_price: minimal acceptable price
        :param max_price: maximal acceptable price
        :param ticks: grouped ticks
        :param is_ask: marks if asks or bids provided as ticks. Defines list to write info.
        """
        adding_list = self.asks if is_ask else self.bids
        for tick_info in ticks:
            tick_price = tick_info[2]
            tick = tick_info[1]
            if min_price <= tick_price <= max_price:
                tick_liquidity_delta = tick_info[0][3]
                liquidity_delta_sign = tick_info[0][4]
                if liquidity_delta_sign:
                    tick_liquidity_delta *= -1
                market_liquidity += tick_liquidity_delta
                adding_list.append(
                    (tick_price, self.calculate_liquidity_amount(tick, market_liquidity))
                )

    def divide_ticks_on_bids_asks(self, ticks_info: list[tuple]) -> tuple[list, list]:
        """
        Dividing ticks on asks and bids for further processing.
        :param ticks_info: List of all ungrouped ticks
        :return: tuple, containing list of asks as first element and list of bids as second
        """
        current_price_formatted = self.tick_current_price
        asks_data, bids_data = [], []
        for group in ticks_info:
            signed_tick = Decimal(group[0] - HAIKO_MAX_TICK)
            tick_price = self.tick_to_price(signed_tick)
            if tick_price > current_price_formatted:
                asks_data.append((group, signed_tick, tick_price))
            else:
                bids_data.append((group, signed_tick, tick_price))
        return asks_data, bids_data

    def calculate_liquidity_amount(self, tick, liquidity_pair_total) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10**self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001") ** tick * (10 ** (self.token_a_decimal - self.token_b_decimal))

    @staticmethod
    def group_ticks_info(ticks_info, n) -> list:
        """
        Group ticks by n elements
        :param ticks_info: plain information ticks information
        :param n: count of elements in one group
        :return: list with ticks grouped
        """
        if n == 0 or len(ticks_info) % n != 0:
            raise ValueError("Ticks info list should be dividable by n")
        args = [iter(ticks_info)] * n
        return list(zip_longest(*args, fillvalue=0))


if __name__ == "__main__":
    token_0 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    order_book = HaikoOrderBook(token_0, token_1)
    asyncio.run(order_book.fetch_price_and_liquidity())
    print(order_book.get_order_book(), "\n")
