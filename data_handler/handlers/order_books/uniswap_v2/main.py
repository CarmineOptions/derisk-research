from decimal import Decimal
import asyncio

from handlers.helpers import get_range
from handlers.order_books.abstractions import OrderBookBase
from handlers.order_books.uniswap_v2.swap_amm import MySwapPool, SwapAmm


class UniswapV2OrderBook(OrderBookBase):
    DEX = "Starknet"

    def __init__(self, token_a: str, token_b: str):
        super().__init__(token_a, token_b)
        self.token_a = token_a
        self.token_b = token_b
        self.pool = None
        self.swap_amm = SwapAmm()
        # setting = MYSWAP_POOL_SETTINGS[f"mySwap: {self.token_a}/{self.token_b} Pool"]
        # self.pool = MySwapPool(setting)

    async def async_fetch_price_and_liquidity(self) -> None:
        # await self.pool.get_data()
        await self.swap_amm.init()
        self.pool = self.swap_amm.pools[self.swap_amm.tokens_to_id(self.token_a, self.token_b)]
        if isinstance(self.pool, MySwapPool):
            await self.pool.get_data()
        self._calculate_order_book()

    def fetch_price_and_liquidity(self) -> None:
        loop = asyncio.get_event_loop()
        # Check if there is a running event loop (e.g., in Jupyter notebook or other async environments)
        if loop.is_running():
            # If there is already a running event loop, create a new one and run it
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(self.async_fetch_price_and_liquidity())
            asyncio.set_event_loop(loop)
        else:
            # If no running event loop, use the current one
            loop.run_until_complete(self.async_fetch_price_and_liquidity())

    def _calculate_order_book(self) -> None:
        # TODO: fix data fetching for another pairs
        if not self.pool:
            raise RuntimeError("Pool is not initialized")
        token_a_reserves = self.pool.tokens[0].balance_converted
        token_b_reserves = self.pool.tokens[1].balance_converted
        current_price = Decimal(token_b_reserves / token_a_reserves)
        # total_liquidity = self.pool.total_lp_supply
        # TODO: add checks for collateral token
        bids_range = get_range(Decimal(0), current_price, Decimal(current_price / 100))
        asks_range = get_range(current_price, current_price * Decimal("1.3"), Decimal(current_price / 100))
        for price in bids_range:
            liquidity = self.pool.supply_at_price(price)
            self.bids.append((price, liquidity))
        for price in asks_range:
            liquidity = self.pool.supply_at_price(price)
            self.asks.append((price, liquidity))

    def calculate_liquidity_amount(self, tick: Decimal, liquidity_pair_total: Decimal) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2 ** 128))
        return liquidity_delta / 10 ** self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        price = ((sqrt_ratio / (Decimal(2) ** 128)) ** 2) * 10 ** (self.token_a_decimal - self.token_b_decimal)
        return price


if __name__ == '__main__':
    token_a = "ETH"
    token_b = (
        "USDC"
    )
    order_book = UniswapV2OrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n")
