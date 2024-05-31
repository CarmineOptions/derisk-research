import asyncio
from decimal import Decimal
from functools import partial

from web_app.order_books.abstractions import OrderBookBase
from web_app.order_books.constants import TOKEN_MAPPING
from web_app.order_books.haiko.api_connector import (
    HaikoAPIConnector,
    HaikoBlastAPIConnector,
)
from web_app.order_books.haiko.logger import get_logger
from web_app.order_books.haiko.histogram import Histogram


class HaikoOrderBook(OrderBookBase):
    DEX = "Haiko"

    def __init__(self, token_a, token_b, apply_filtering: bool = False):
        super().__init__(token_a, token_b)
        # self.current_price = Decimal("0")
        self.haiko_connector = HaikoAPIConnector()
        self.blast_connector = HaikoBlastAPIConnector()
        self.apply_filtering = apply_filtering
        self.logger = get_logger("./logs", echo=True)

        self.token_a_name = TOKEN_MAPPING.get(token_a).name
        self.token_b_name = TOKEN_MAPPING.get(token_b).name
        self.token_a_price = Decimal(0)
        self.token_b_price = Decimal(0)

        self._decimals_diff = 10 ** (self.token_a_decimal - self.token_b_decimal or self.token_a_decimal)
        self._check_tokens_supported()
        self._set_usd_prices()

    def _set_usd_prices(self) -> None:
        prices = self.haiko_connector.get_usd_prices(self.token_a_name, self.token_b_name)
        self.token_a_price = Decimal(prices.get(self.token_a_name, 0))
        self.token_b_price = Decimal(prices.get(self.token_b_name, 0))
        if self.token_a_price == 0 or self.token_b_price == 0:
            raise RuntimeError("Prices for tokens aren't available.")

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

    def set_current_price(self, current_price: Decimal) -> None:
        """
        Set the current price based on the current tick.
        :param current_price: Decimal - Current market price
        """
        self.tick_current_price = current_price

    def sort_asks_bids(self) -> None:
        """Sort bids and asks data in correct order."""
        self.asks.sort(key=lambda ask: ask[0])
        self.bids.sort(key=lambda bid: bid[0], reverse=True)

    async def fetch_price_and_liquidity(self) -> None:
        tokens_markets = self.haiko_connector.get_pair_markets(self.token_a, self.token_b)
        tokens_markets = self._filter_markets_data(tokens_markets)
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
            self._calculate_order_book(market_depth_list, Decimal(market["currPrice"]))

        self.sort_asks_bids()
        self.tick_current_price = max(tokens_markets, key=lambda x: Decimal(x["tvl"]))["currPrice"]

    def _filter_asks_bids(self, asks: list, bids, min_price: Decimal, max_price: Decimal) -> tuple:
        """
        Filter asks and bids from the market liquidity data.
        :param asks: list - List of asks data
        :param bids: list - List of bids data
        :param min_price: Decimal - Minimal acceptable price
        :param max_price: Decimal - Maximal acceptable price
        :return: tuple - Tuple of filtered asks and bids
        """
        asks = [tick for tick in asks if min_price < tick["price"] < max_price]
        bids = [tick for tick in bids if min_price < tick["price"] < max_price]
        return asks, bids

    def _calculate_order_book(
        self, market_ticks_liquidity: list, current_price: Decimal
    ) -> None:
        self.set_current_price(current_price)
        price_range = self.calculate_price_range()
        asks, bids = [], []
        for tick_info in market_ticks_liquidity:
            tick_info["price"] = Decimal(tick_info["price"])
            tick_info["liquidityCumulative"] = Decimal(tick_info["liquidityCumulative"])
            if tick_info["price"] >= current_price:
                asks.append(tick_info)
            else:
                bids.append(tick_info)

        if not asks or not bids:
            return

        bids.sort(key=lambda x: x["price"], reverse=True)
        asks.sort(key=lambda x: x["price"])
        self.add_bids(bids, price_range)
        self.add_asks(asks, bids[0]["liquidityCumulative"], price_range)

    def add_asks(
            self, market_asks: list[dict], pool_liquidity: Decimal, price_range: tuple
    ) -> None:
        """
        Add `asks` to the order book.
        :param market_asks: list of dictionaries with price and liquidityCumulative
        :param pool_liquidity: current liquidity in a pool
        :param price_range: tuple of Decimal - minimal and maximal acceptable prices
        """
        if not market_asks:
            return
        local_asks = []
        x = self._get_token_amount(
            pool_liquidity,
            self.tick_current_price.sqrt(),
            market_asks[0]['price'].sqrt(),
        )
        local_asks.append((self.tick_current_price, x))
        for index, ask in enumerate(market_asks):
            if index == 0:
                continue
            current_price = Decimal(market_asks[index - 1]['price'])
            x = self._get_token_amount(
                Decimal(market_asks[index - 1]['liquidityCumulative']),
                current_price.sqrt(),
                Decimal(market_asks[index]['price']).sqrt(),
            )
            local_asks.append((current_price, x))
        if self.apply_filtering:
            self.asks.extend([ask for ask in local_asks if price_range[0] < ask[0] < price_range[1]])
            return
        self.asks.extend(local_asks)

    def add_bids(
            self, market_bids: list[dict], price_range: tuple
    ) -> None:
        """
        Add `bids` to the order book.
        :param price_range: tuple of Decimal - minimal and maximal acceptable prices
        :param market_bids: list of dictionaries with price and liquidityCumulative
        """
        if not market_bids:
            return
        local_bids = []
        prev_price = Decimal(market_bids[0]['price'])
        y = self._get_token_amount(
            Decimal(market_bids[0]['liquidityCumulative']),
            self.tick_current_price.sqrt(),
            prev_price.sqrt(),
            is_ask=False
        )
        local_bids.append((prev_price, y))
        for index, bid in enumerate(market_bids[::-1]):
            if index == 0:
                continue
            current_price = Decimal(market_bids[index - 1]['price'])
            y = self._get_token_amount(
                Decimal(market_bids[index]['liquidityCumulative']),
                current_price.sqrt(),
                Decimal(market_bids[index]['price']).sqrt(),
                is_ask=False
            )
            local_bids.append((current_price, y))
        if self.apply_filtering:
            self.bids.extend([bid for bid in local_bids if price_range[0] < bid[0] < price_range[1]])
            return
        self.bids.extend(local_bids)

    def _get_token_amount(
            self, current_liq: Decimal, current_sqrt: Decimal, next_sqrt: Decimal, is_ask: bool = True
    ) -> Decimal:
        """
        Calculate token amount based on liquidity data and current data processed(asks/bids).
        :param current_liq: Decimal - Current price liquidity
        :param current_sqrt: Decimal - Current square root of a price
        :param next_sqrt: Decimal - Next square root of a price
        :param is_ask: bool - True if an ask data
        """
        if is_ask:
            amount = abs(current_liq / next_sqrt - current_liq / current_sqrt)
        else:
            amount = abs(current_liq * next_sqrt - current_liq * current_sqrt)
        return amount / self._decimals_diff

    def _get_sqrt_ratio(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001").sqrt() ** tick

    def calculate_liquidity_amount(self, tick, liquidity_pair_total) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10 ** self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001") ** tick * (10 ** (self.token_a_decimal - self.token_b_decimal))

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


if __name__ == "__main__":
    # token_0 = "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"  # STRK
    # token_1 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    # token_0 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    # token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    # token_0 = "0x42b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2"  # wstETH
    # token_1 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_0 = "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"  # STRK
    token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC

    order_book = HaikoOrderBook(token_0, token_1)
    asyncio.run(order_book.fetch_price_and_liquidity())
    histogram = Histogram(order_book)
    histogram.show_asks()
    # histogram.show_bids()
    print()
