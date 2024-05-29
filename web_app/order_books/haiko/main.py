import asyncio
import math
from decimal import Decimal
from functools import partial

from matplotlib import pyplot as plt

from src.blockchain_call import func_call
from web_app.order_books.abstractions import OrderBookBase
from web_app.order_books.haiko.api_connector import (
    HaikoAPIConnector,
    HaikoBlastAPIConnector,
)
from web_app.order_books.haiko.logger import get_logger

HAIKO_MARKET_MANAGER_ADDRESS = "0x0038925b0bcf4dce081042ca26a96300d9e181b910328db54a6c89e5451503f5"
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

    def set_current_price(self, current_tick: Decimal) -> None:
        """
        Set the current price based on the current tick.
        :param current_tick: Int - Current tick
        """
        self.tick_current_price = self.tick_to_price(current_tick)

    def sort_asks_bids(self) -> None:
        """Sort bids and asks data in correct order."""
        self.asks.sort(key=lambda ask: ask[0])
        self.bids.sort(key=lambda bid: bid[0])

    async def fetch_price_and_liquidity(self) -> None:
        tokens_markets = self.haiko_connector.get_pair_markets(self.token_a, self.token_b)
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
            market_depth_list = self.haiko_connector.get_market_depth(market_id)
            if not market_depth_list:
                self.logger.info(f"Market depth for market {market_id} is empty.")
                continue
            liquidity = await func_call(HAIKO_MARKET_MANAGER_ADDRESS, "liquidity", [market_id])
            self._calculate_order_book(
                Decimal(liquidity[0]), Decimal(market["width"]), market_depth_list, Decimal(market["currLimit"])
            )
            r = sum(info[1] for info in self.asks)
            print()

        self.sort_asks_bids()
        self.filter_asks_bids()
        self.current_price = max(tokens_markets, key=lambda x: Decimal(x["tvl"]))["currPrice"]

    def filter_asks_bids(self) -> None:
        min_ask_price = self.asks[1][0]
        self.asks = self.asks[1:] if self.asks[0][0] == 0 else self.asks
        self.bids = list(filter(lambda bid: bid[0] < min_ask_price, self.bids))

    def _calculate_order_book(
        self, liquidity: Decimal, tick_spacing: Decimal, market_ticks_liquidity: list, current_tick: Decimal
    ) -> None:
        self.set_current_price(current_tick)
        min_price, max_price = self.calculate_price_range()
        asks, bids = [], []
        for tick_info in market_ticks_liquidity:
            if Decimal(tick_info["price"]) == 0:
                continue
            tick = self.price_to_tick(Decimal(tick_info["price"]))
            tick_info["tick"] = tick
            if tick >= current_tick:
                asks.append(tick_info)
            else:
                bids.append(tick_info)

        self.add_asks(asks, liquidity, current_tick, tick_spacing)
        self.add_bids(bids, liquidity, current_tick, tick_spacing)

        self.asks = [
            (price, supply)
            for price, supply in self.asks
            if min_price < price < max_price
        ]
        self.bids = [
            (price, supply)
            for price, supply in self.bids
            if min_price < price < max_price
        ]
        # process_ticks = partial(self.process_ticks, min_price, max_price)
        # asks, bids = self.divide_ticks_on_bids_asks(liquidity, market_ticks_liquidity)
        # process_ticks(asks, is_ask=True)
        # process_ticks(bids, is_ask=False)

    def add_asks(
            self, liquidity_data: list[dict], liquidity: Decimal, current_tick: Decimal, tick_spacing: Decimal
    ) -> None:
        """
        Add `asks` to the order book.
        :param liquidity_data: list of dict with tick and net_liquidity_delta_diff
        :param row: pool row data
        """
        # ask_ticks = [i for i in liquidity_data if i["tick"] >= current_tick]
        if not liquidity_data:
            return

        glob_liq = Decimal(liquidity_data[0]["liquidityCumulative"])

        # Calculate for current tick (loops start with the next one)
        next_tick = liquidity_data[0]["tick"]
        prev_tick = next_tick - tick_spacing

        prev_sqrt = self._get_sqrt_ratio(prev_tick)
        next_sqrt = self._get_sqrt_ratio(next_tick)

        supply = abs(
            ((glob_liq / prev_sqrt) - (glob_liq / next_sqrt)) / (10 ** self.token_a_decimal)
        )
        price = self.tick_to_price(prev_tick)
        self.asks.append((price, supply))

        for index, tick in enumerate(liquidity_data):
            if index == 0:
                continue
            # glob_liq += Decimal(liquidity_data[index - 1]["liquidityCumulative"])
            glob_liq = Decimal(liquidity_data[index - 1]["liquidityCumulative"])
            prev_tick = Decimal(liquidity_data[index - 1]["tick"])
            curr_tick = Decimal(tick["tick"])

            prev_sqrt = self._get_sqrt_ratio(prev_tick)
            next_sqrt = self._get_sqrt_ratio(curr_tick)

            supply = abs(
                ((glob_liq / prev_sqrt) - (glob_liq / next_sqrt))
                / 10 ** self.token_a_decimal
            )
            price = self.tick_to_price(prev_tick)
            self.asks.append((price, supply))

    def add_bids(
            self, liquidity_data: list[dict], liquidity: Decimal, current_tick: Decimal, tick_spacing: Decimal
    ) -> None:
        """
        Add `bids` to the order book.
        :param liquidity_data: liquidity data list of dict with tick and net_liquidity_delta_diff
        :param row: pool row data
        """
        # bid_ticks = [i for i in liquidity_data if i["tick"] <= row["tick"]][::-1]
        # if not bid_ticks:
        #     return

        glob_liq = Decimal(liquidity_data[0]["liquidityCumulative"])

        next_tick = liquidity_data[0]["tick"]
        prev_tick = next_tick + tick_spacing

        prev_sqrt = self._get_sqrt_ratio(prev_tick)
        next_sqrt = self._get_sqrt_ratio(next_tick)

        supply = abs(
            ((glob_liq * prev_sqrt) - (glob_liq * next_sqrt)) / 10**self.token_b_decimal
        )
        price = self.tick_to_price(prev_tick)
        self.bids.append((price, supply))

        for index, tick in enumerate(liquidity_data):
            if index == 0:
                continue
            glob_liq -= Decimal(liquidity_data[index - 1]["liquidityCumulative"])
            # glob_liq = Decimal(liquidity_data[index - 1]["liquidityCumulative"])
            prev_tick = Decimal(liquidity_data[index - 1]["tick"])
            curr_tick = Decimal(tick["tick"])

            prev_sqrt = self._get_sqrt_ratio(prev_tick)
            next_sqrt = self._get_sqrt_ratio(curr_tick)

            supply = (
                abs(((glob_liq * prev_sqrt) - (glob_liq * next_sqrt)))
                / 10**self.token_b_decimal
            )
            price = self.tick_to_price(prev_tick)
            self.bids.append((price, supply))

    def process_ticks(
        self,
        min_price: Decimal,
        max_price: Decimal,
        depth: list[tuple[Decimal, Decimal]],
        is_ask=True,
    ) -> None:
        """
        Process ticks and add info about price and liquidity to correct list.
        :param min_price: minimal acceptable price
        :param max_price: maximal acceptable price
        :param depth: market depth information
        :param is_ask: marks if asks or bids provided as ticks. Defines list to write info.
        """
        adding_list = self.asks if is_ask else self.bids
        for depth_entry in depth:
            price = Decimal(depth_entry[0])
            if price == 0:
                continue
            base_log = math.log(1.00001)
            base_price_log = math.log(price / 10 ** Decimal(self.token_a_decimal - self.token_b_decimal))
            tick = round(base_price_log / base_log)
            liquidity_amount = self.calculate_liquidity_amount(tick, Decimal(depth_entry[1]))
            if min_price <= price <= max_price:
                adding_list.append((price, liquidity_amount))

    def _get_sqrt_ratio(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001").sqrt() ** tick

    def price_to_tick(self, price: Decimal) -> Decimal:
        return Decimal(math.log(price / (10 ** (self.token_a_decimal - self.token_b_decimal))) / math.log(1.00001))

    def divide_ticks_on_bids_asks(self, liquidity: Decimal, total_depth: list[dict]) -> tuple[list, list]:
        """
        Dividing ticks on asks and bids for further processing.
        :param total_depth: List of all ungrouped ticks
        :return: tuple, containing list of asks as first element and list of bids as second
        """
        current_price_formatted = self.tick_current_price
        asks_data, bids_data = [], []
        for current_depth in total_depth:
            price = Decimal(current_depth["price"])
            if price > current_price_formatted:
                liquidity += Decimal(current_depth["liquidityCumulative"])
                asks_data.append((price, liquidity))
            else:
                liquidity -= Decimal(current_depth["liquidityCumulative"])
                bids_data.append((price, liquidity))
        return asks_data, bids_data

    def calculate_liquidity_amount(self, tick, liquidity_pair_total) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10 ** self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001") ** tick * (10 ** (self.token_a_decimal - self.token_b_decimal))




if __name__ == "__main__":
    token_0 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    order_book = HaikoOrderBook(token_0, token_1)
    asyncio.run(order_book.fetch_price_and_liquidity())

    # data = order_book.get_order_book()
    # print()
    # bid_prices, bid_amounts = zip(*data["bids"])
    # ask_prices, ask_amounts = zip(*data["asks"])
    #
    # fig, ax = plt.subplots()
    #
    # # ax.bar(bid_prices, bid_amounts, width=10, color='green', label='Bids')
    #
    # ax.bar(ask_prices, ask_amounts, width=10, color='red', label='Asks')
    #
    # spread_start = max(bid_prices)
    # spread_end = min(ask_prices)
    # ax.axvspan(spread_start, spread_end, color='grey', alpha=0.5)
    # # ax.set_yscale('log')
    # ax.set_xlabel('Price')
    # ax.set_ylabel('Liquidity Amount')
    # ax.set_title('Order Book Histogram')
    # ax.legend()
    #
    # plt.show()

    # histogram = Histogram()
    # # histogram.show_asks()
    # histogram.show_bids()
