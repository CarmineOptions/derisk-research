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
            self._calculate_order_book(market_depth_list, Decimal(market["currLimit"]))

        self.sort_asks_bids()
        self.filter_asks_bids()
        self.current_price = max(tokens_markets, key=lambda x: Decimal(x["tvl"]))["currPrice"]

    def filter_asks_bids(self) -> None:
        min_ask_price = self.asks[1][0]
        self.asks = self.asks[1:] if self.asks[0][0] == 0 else self.asks
        self.bids = list(filter(lambda bid: bid[0] < min_ask_price, self.bids))

    def _calculate_order_book(
        self, market_ticks_liquidity: list, current_tick: Decimal
    ) -> None:
        tvl = Decimal("0")
        self.set_current_price(current_tick)
        min_price, max_price = self.calculate_price_range()
        process_ticks = partial(self.process_ticks, min_price, max_price)
        asks, bids = self.divide_ticks_on_bids_asks(market_ticks_liquidity)
        for group in asks:
            tvl += (Decimal(group[1]) * self.tick_current_price)
        process_ticks(asks, is_ask=True)
        process_ticks(bids, is_ask=False)

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

    def divide_ticks_on_bids_asks(self, total_depth: list[dict]) -> tuple[list, list]:
        """
        Dividing ticks on asks and bids for further processing.
        :param total_depth: List of all ungrouped ticks
        :return: tuple, containing list of asks as first element and list of bids as second
        """
        current_price_formatted = self.tick_current_price
        asks_data, bids_data = [], []
        for current_depth in total_depth:
            price = Decimal(current_depth["price"])
            liquidity = Decimal(current_depth["liquidityCumulative"])
            grouped_info = (price, liquidity)
            if price > current_price_formatted:
                asks_data.append(grouped_info)
            else:
                bids_data.append(grouped_info)
        return asks_data, bids_data

    def calculate_liquidity_amount(self, tick, liquidity_pair_total) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10 ** self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001") ** tick * (10 ** (self.token_a_decimal - self.token_b_decimal))


if __name__ == "__main__":
    token_0 = "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"  # ETH
    token_1 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # USDC
    order_book = HaikoOrderBook(token_0, token_1)
    asyncio.run(order_book.fetch_price_and_liquidity())
    # print(order_book.get_order_book(), "\n")
    data = order_book.get_order_book()
    # data["asks"] = [[float(ask[0]), float(ask[1]) * 10 ** 5] for ask in data["asks"]]
    # data["bids"] = [[float(bid[0]), float(bid[1]) * 10 ** 5] for bid in data["bids"]]
    print()
    bid_prices, bid_amounts = zip(*data["bids"])
    ask_prices, ask_amounts = zip(*data["asks"])

    # Define the range for the x-axis

    # Create figure and axis
    fig, ax = plt.subplots()

    # Plot bids
    ax.bar(bid_prices, bid_amounts, width=0.000001, color='green', label='Bids')

    # Plot asks
    ax.bar(ask_prices, ask_amounts, width=0.000001, color='red', label='Asks')

    # Highlight the spread zone
    spread_start = max(bid_prices)
    spread_end = min(ask_prices)
    ax.axvspan(spread_start, spread_end, color='grey', alpha=0.5)
    ax.set_yscale('log')
    # Labels and title
    ax.set_xlabel('Price')
    ax.set_ylabel('Liquidity Amount')
    ax.set_title('Order Book Histogram')
    ax.legend()

    # Display the plot
    plt.show()
