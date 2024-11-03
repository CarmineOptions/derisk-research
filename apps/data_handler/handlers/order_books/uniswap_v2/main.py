""" This module contains the main class for the Uniswap V2 order book. """
import asyncio
from decimal import Decimal
from typing import Iterable

from data_handler.handlers.helpers import get_collateral_token_range, get_range
from data_handler.handlers.order_books.abstractions import OrderBookBase
from data_handler.handlers.order_books.uniswap_v2.swap_amm import SwapAmm


class UniswapV2OrderBook(OrderBookBase):
    """ This module contains the main class for the Uniswap V2 order book. """
    DEX = "Starknet"

    def __init__(self, token_a: str, token_b: str):
        super().__init__(token_a, token_b)
        self.token_a = token_a
        self.token_b = token_b
        self.token_a_name = None
        self.token_b_name = None
        self._pool = None
        self._swap_amm = SwapAmm()
        self._set_token_names()

    def _set_token_names(self) -> None:
        """Get token names from token addresses."""
        token_a_info, token_b_info = self.get_token_configs()
        self.token_a_name = token_a_info.name
        self.token_b_name = token_b_info.name

    def _set_current_price(self) -> None:
        """Set the current price of the pair based on asks and bids."""
        if not self.asks or not self.bids:
            raise ValueError("Asks and bids are required to calculate the current price.")
        max_bid_price = max(self.bids, key=lambda x: x[0])[0]
        min_ask_price = min(self.asks, key=lambda x: x[0])[0]
        self.current_price = (max_bid_price + min_ask_price) / Decimal("2")

    def _set_pool(self) -> None:
        """Retrieve and set pool from available pools."""
        tokens_id = self._swap_amm.tokens_to_id(self.token_a_name, self.token_b_name)
        if tokens_id not in self._swap_amm.pools:
            raise ValueError(f"Pool {tokens_id} not found.")
        self._pool = self._swap_amm.pools[tokens_id]

    async def _async_fetch_price_and_liquidity(self) -> None:
        """Asynchronous implementation of the abstract method to fetch price and liquidity data."""
        await self._swap_amm.init()
        self._set_pool()
        self._calculate_order_book()

    def fetch_price_and_liquidity(self) -> None:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(self._async_fetch_price_and_liquidity())
            asyncio.set_event_loop(loop)
        else:
            loop.run_until_complete(self._async_fetch_price_and_liquidity())

    def get_prices_range(self, current_price: Decimal) -> Iterable[Decimal]:
        """
        Get prices range based on the current price.
        :param current_price: Decimal - The current pair price.
        :return: Iterable[Decimal] - The iterable prices range.
        """
        collateral_tokens = ("ETH", "wBTC", "STRK")
        if self.token_a in collateral_tokens:
            return get_collateral_token_range(self.token_a, current_price)
        return get_range(Decimal(0), current_price * Decimal("1.3"), Decimal(current_price / 100))

    def _calculate_order_book(self) -> None:
        token_a_reserves = Decimal(self._pool.tokens[0].balance_converted)
        token_b_reserves = Decimal(self._pool.tokens[1].balance_converted)
        if token_a_reserves == 0 or token_b_reserves == 0:
            raise RuntimeError("Reserves can't be zero")
        current_price = token_b_reserves / token_a_reserves
        prices_range = self.get_prices_range(current_price)
        self.add_quantities_data(prices_range, current_price)
        self._set_current_price()
        self.block = 0

    def add_quantities_data(self, prices_range: Iterable[Decimal], current_price: Decimal) -> None:
        """
        Add bids and asks data to the order book.
        :param prices_range: Iterable[Decimal] - The prices range to get quantities for.
        :param current_price: Decimal - The current pair price.
        """
        if current_price == 0:
            raise ValueError("Provide valid prices range and current price for analysis.")
        for price in prices_range:
            supply = self._pool.supply_at_price(price)
            if price < current_price:
                self.bids.append((price, supply))
            else:
                self.asks.append((price, supply))

    def calculate_liquidity_amount(self, tick: Decimal, liquidity_pair_total: Decimal) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10**self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        price = ((sqrt_ratio /
                  (Decimal(2)**128))**2) * 10**(self.token_a_decimal - self.token_b_decimal)
        return price


if __name__ == "__main__":
    token_0 = "ETH"
    token_1 = "USDC"
    order_book = UniswapV2OrderBook(token_0, token_1)
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n")
