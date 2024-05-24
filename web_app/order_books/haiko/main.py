import asyncio
from decimal import Decimal

from src.blockchain_call import func_call
from web_app.order_books.abstractions import OrderBookBase
from web_app.order_books.haiko.api_connector import HaikoAPIConnector

HAIKO_MARKET_MANAGER_ADDRESS = "0x0038925b0bcf4dce081042ca26a96300d9e181b910328db54a6c89e5451503f5"


class HaikoOrderBook(OrderBookBase):
    DEX = "Haiko"

    def __init__(self, token_a, token_b):
        super().__init__(token_a, token_b)
        self.connector = HaikoAPIConnector()
        self._check_tokens_supported()

    def _check_tokens_supported(self) -> None:
        supported_tokens = self.connector.get_supported_tokens()
        if isinstance(supported_tokens, dict) and supported_tokens.get("error"):
            raise RuntimeError(f"Unexpected error from API: {supported_tokens}")
        supported_tokens_filtered = [token for token in supported_tokens if token["address"] in (self.token_a, self.token_b)]
        if len(supported_tokens_filtered) != 2:
            raise ValueError("One of tokens isn't supported by Haiko")

    def _filter_markets_data(self, all_markets_data: list) -> list:
        return list(filter(
            lambda market: market["baseToken"]["address"] == self.token_a and
            market["quoteToken"]["address"] == self.token_b,
            all_markets_data
        ))

    async def _get_market_ticks_liquidity(self, market_id) -> list: # noqa
        try:
            return await func_call(HAIKO_MARKET_MANAGER_ADDRESS, "depth", [market_id])
        except Exception as e:
            print(f"Failed for market ID: {market_id}")
            return []

    def set_current_price(self, current_tick: Decimal) -> None:
        """
        Set the current price based on the current tick.
        :param current_tick: Int - Current tick
        """
        self.tick_current_price = self.tick_to_price(current_tick)

    async def fetch_price_and_liquidity(self) -> None:
        all_markets_data = self.connector.get_token_markets()
        if isinstance(all_markets_data, dict) and all_markets_data.get("error"):
            raise RuntimeError(f"Unexpected error from API: {all_markets_data}")

        tokens_markets = self._filter_markets_data(all_markets_data)
        if not tokens_markets:
            raise RuntimeError("Markets for this pair isn't available for now")
        for market in tokens_markets:
            market_id = market["market_id"]
            liquidity = await func_call(HAIKO_MARKET_MANAGER_ADDRESS, "liquidity", [market_id])
            market_ticks_liquidity = await self._get_market_ticks_liquidity(market_id)
            if not market_ticks_liquidity:
                continue
            self._calculate_order_book(market_ticks_liquidity, liquidity, market["currLimit"])

    def _calculate_order_book(self, market_ticks_liquidity: list, liquidity: Decimal, current_tick: Decimal) -> tuple:
        self.set_current_price(current_tick)
        min_price, max_price = self.calculate_price_range()

    def calculate_liquidity_amount(self, *args, **kwargs) -> Decimal:
        pass

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001") ** tick * (10 ** (self.token_a_decimal - self.token_b_decimal))


if __name__ == '__main__':
    token_0 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    order_book = HaikoOrderBook(token_0, token_1)
    # print(order_book.tick_to_price(Decimal(-1939491)) * 10 ** 16)
    order_book.fetch_price_and_liquidity()
    # print((Decimal("1.00001").sqrt() ** -1939491) * 10 ** 24)
