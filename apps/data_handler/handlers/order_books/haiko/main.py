""" Haiko Order Book class implementation """
from decimal import Decimal
from pathlib import Path

from data_handler.handlers.order_books.abstractions import OrderBookBase
from data_handler.handlers.order_books.constants import TOKEN_MAPPING
from data_handler.handlers.order_books.haiko.api_connector import (
    HaikoAPIConnector,
    HaikoBlastAPIConnector,
)
from data_handler.handlers.order_books.haiko.logger import get_logger


class HaikoOrderBook(OrderBookBase):
    """ Haiko Order Book class. """
    DEX = "Haiko"

    def __init__(self, token_a, token_b, apply_filtering: bool = False):
        """
        Initialize the HaikoOrderBook object.
        :param token_a: baseToken hexadecimal address
        :param token_b: quoteToken hexadecimal address
        :param apply_filtering: bool - 
        If True apply min and max price filtering to the order book data
        """
        super().__init__(token_a, token_b)
        self.haiko_connector = HaikoAPIConnector()
        self.blast_connector = HaikoBlastAPIConnector()
        self.apply_filtering = apply_filtering
        self.logger = get_logger("Haiko", Path().resolve().joinpath("./logs"), echo=True)

        self.token_a_price = Decimal(0)
        self.token_b_price = Decimal(0)

        self._decimals_diff = 10**(
            self.token_a_decimal - self.token_b_decimal or self.token_a_decimal
        )
        self._check_tokens_supported()
        self._set_usd_prices()

    def _get_valid_tokens_addresses(self) -> tuple[str, str]:
        """
        Get tokens' addresses without leading zeros.
        :return: tuple - The token addresses tuple without leading zeros
        """
        if not isinstance(self.token_a, str) or not isinstance(self.token_b, str):
            raise ValueError("Token addresses must be strings.")
        return hex(int(self.token_a, base=16)), hex(int(self.token_b, base=16))

    def _set_usd_prices(self) -> None:
        """Set USD prices for tokens based on Haiko API."""
        token_a_info = TOKEN_MAPPING.get(self.token_a)
        token_b_info = TOKEN_MAPPING.get(self.token_b)
        if not token_a_info or not token_b_info:
            raise ValueError("Information about tokens isn't available.")
        token_a_name = token_a_info.name
        token_b_name = token_b_info.name
        prices = self.haiko_connector.get_usd_prices(token_a_name, token_b_name)
        self.token_a_price = Decimal(prices.get(token_a_name, 0))
        self.token_b_price = Decimal(prices.get(token_b_name, 0))
        if self.token_a_price == 0 or self.token_b_price == 0:
            raise RuntimeError("Prices for tokens aren't available.")

    def _check_tokens_supported(self) -> None:
        """Check if a pair of tokens is supported by Haiko"""
        supported_tokens = self.haiko_connector.get_supported_tokens(existing_only=False)
        if isinstance(supported_tokens, dict) and supported_tokens.get("error"):
            raise RuntimeError(f"Unexpected error from API: {supported_tokens}")
        valid_tokens = self._get_valid_tokens_addresses()
        supported_tokens_filtered = [
            token for token in supported_tokens if token["address"] in valid_tokens
        ]
        if len(supported_tokens_filtered) != 2:
            raise ValueError("One of tokens isn't supported by Haiko")

    def set_current_price(self, current_price: Decimal) -> None:
        """
        Set the current price based on the current tick.
        :param current_price: Decimal - Current market price
        """
        self.current_price = current_price

    def sort_asks_bids(self) -> None:
        """Sort bids and asks data in correct order."""
        self.asks.sort(key=lambda ask: ask[0])
        self.bids.sort(key=lambda bid: bid[0], reverse=True)

    def fetch_price_and_liquidity(self) -> None:
        tokens_markets = self._filter_markets_data(
            self.haiko_connector.get_pair_markets(self.token_a, self.token_b)
        )
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
        self.current_price = max(tokens_markets, key=lambda x: Decimal(x["tvl"]))["currPrice"]

    def _calculate_order_book(self, market_ticks_liquidity: list, current_price: Decimal) -> None:
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
            self.current_price.sqrt(),
            market_asks[0]["price"].sqrt(),
        )
        local_asks.append((self.current_price, x))
        for index, ask in enumerate(market_asks):
            if index == 0:
                continue
            current_price = Decimal(market_asks[index - 1]["price"])
            x = self._get_token_amount(
                Decimal(market_asks[index - 1]["liquidityCumulative"]),
                current_price.sqrt(),
                Decimal(market_asks[index]["price"]).sqrt(),
            )
            local_asks.append((current_price, x))
        if self.apply_filtering:
            self.asks.extend(
                [ask for ask in local_asks if price_range[0] < ask[0] < price_range[1]]
            )
            return
        self.asks.extend(local_asks)

    def add_bids(self, market_bids: list[dict], price_range: tuple) -> None:
        """
        Add `bids` to the order book.
        :param market_bids: list of dictionaries with price and liquidityCumulative
        :param price_range: tuple of Decimal - minimal and maximal acceptable prices
        """
        if not market_bids:
            return
        local_bids = []
        prev_price = Decimal(market_bids[0]["price"])
        y = self._get_token_amount(
            Decimal(market_bids[0]["liquidityCumulative"]),
            self.current_price.sqrt(),
            prev_price.sqrt(),
            is_ask=False,
        )
        local_bids.append((prev_price, y))
        for index, bid in enumerate(market_bids[::-1]):
            if index == 0:
                continue
            current_price = Decimal(market_bids[index - 1]["price"])
            y = self._get_token_amount(
                Decimal(market_bids[index]["liquidityCumulative"]),
                current_price.sqrt(),
                Decimal(market_bids[index]["price"]).sqrt(),
                is_ask=False,
            )
            local_bids.append((current_price, y))
        if self.apply_filtering:
            self.bids.extend(
                [bid for bid in local_bids if price_range[0] < bid[0] < price_range[1]]
            )
            return
        self.bids.extend(local_bids)

    def _get_token_amount(
        self,
        current_liq: Decimal,
        current_sqrt: Decimal,
        next_sqrt: Decimal,
        is_ask: bool = True,
    ) -> Decimal:
        """
        Calculate token amount based on liquidity data and current data processed(asks/bids).
        :param current_liq: Decimal - Current price liquidity
        :param current_sqrt: Decimal - Current square root of a price
        :param next_sqrt: Decimal - Next square root of a price
        :param is_ask: bool - True if an ask data
        :return: Decimal - token amount
        """
        if is_ask and (current_sqrt == 0 or next_sqrt == 0):
            raise ValueError("Square root of prices for asks can't be zero.")
        if not is_ask and next_sqrt == 0:
            return abs(current_liq / current_sqrt) / self._decimals_diff
        amount = abs(current_liq / next_sqrt - current_liq / current_sqrt)
        return amount / self._decimals_diff

    def calculate_liquidity_amount(self, tick, liquidity_pair_total) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10**self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001")**tick * (10**(self.token_a_decimal - self.token_b_decimal))

    def _filter_markets_data(self, all_markets_data: list) -> list:
        """
        Filter markets for actual token pair.
        :param all_markets_data: all supported markets provided bt Haiko
        :return: list of markets data for actual token pair
        """
        token_a_valid, token_b_valid = self._get_valid_tokens_addresses()
        return list(
            filter(
                lambda market: market["baseToken"]["address"] == token_a_valid and market[
                    "quoteToken"]["address"] == token_b_valid,
                all_markets_data,
            )
        )


if __name__ == "__main__":
    # token_0 = "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"  # STRK
    # token_1 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    # token_0 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    # token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    token_0 = (
        "0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2"  # wstETH
    )
    token_1 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    # token_0 = "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d"  # STRK
    # token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    # token_0 = "0x07e2c010c0b381f347926d5a203da0335ef17aefee75a89292ef2b0f94924864"  # wstETH
    # token_1 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"
    # token_1 = "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8"
    order_book = HaikoOrderBook(token_0, token_1)
    order_book.fetch_price_and_liquidity()
    serialized_order_book = order_book.serialize()
