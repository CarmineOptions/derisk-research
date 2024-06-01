from decimal import Decimal
import asyncio
from handlers.order_books.abstractions import OrderBookBase
from .swap_amm import MySwapPool, SwapAmm



class UniswapV2OrderBook(OrderBookBase):
    DEX = "Starkets"

    def __init__(self, token_a: str, token_b: str):
        super().__init__(token_a, token_b)
        self.token_a = token_a
        self.token_b = token_b
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
        token_a_reserves = self.pool.token_amounts.values[self.token_a]
        token_b_reserves = self.pool.token_amounts.values[self.token_b]
        total_liquidity = self.pool.total_lp_supply

        token_a = self.pool.tokens[0]
        token_b = self.pool.tokens[1]

        # Calculate the constant product
        constant_product = token_a_reserves * token_b_reserves

        # Add (price, token_a_amount) to self.asks
        self.asks.append((token_a.balance_converted, token_a.balance_converted))

        # Calculate token_b_amount using the constant product formula
        token_b_amount = constant_product / (token_a_reserves + token_a.balance_converted)

        # Add (price, token_b_amount) to self.bids
        self.bids.append((token_a.balance_converted, token_b_amount))

        # Repeat the process for token_b
        # Add (price, token_b_amount) to self.asks
        self.asks.append((token_b.balance_converted, token_b.balance_converted))

        # Calculate token_a_amount using the constant product formula
        token_a_amount = constant_product / (token_b_reserves + token_b.balance_converted)

        # Add (price, token_a_amount) to self.bids
        self.bids.append((token_b.balance_converted, token_a_amount))

        # Calculate total liquidity
        self.total_liquidity = total_liquidity

    def calculate_liquidity_amount(self, tick: Decimal, liquidity_pair_total: Decimal) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2 ** 128))
        return liquidity_delta / 10 ** self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        price = ((sqrt_ratio / (Decimal(2) ** 128)) ** 2) * 10 ** (self.token_a_decimal - self.token_b_decimal)
        return price


if __name__ == '__main__':
    token_a = "ETH"  #
    token_b = (
        "USDC"  #
    )
    order_book = UniswapV2OrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n")

    