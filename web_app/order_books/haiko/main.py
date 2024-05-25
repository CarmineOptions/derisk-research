import asyncio
from decimal import Decimal
from functools import partial
from itertools import zip_longest

from src.blockchain_call import func_call
from web_app.order_books.abstractions import OrderBookBase
from web_app.order_books.haiko.api_connector import HaikoAPIConnector

HAIKO_MARKET_MANAGER_ADDRESS = "0x0038925b0bcf4dce081042ca26a96300d9e181b910328db54a6c89e5451503f5"
HAIKO_MAX_TICK = 7906205


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
        supported_tokens_filtered = [
            token for token in supported_tokens if token["address"] in (self.token_a, self.token_b)
        ]
        if len(supported_tokens_filtered) != 2:
            raise ValueError("One of tokens isn't supported by Haiko")

    def _filter_markets_data(self, all_markets_data: list) -> list:
        return list(filter(
            lambda market: market["baseToken"]["address"] == self.token_a and
            market["quoteToken"]["address"] == self.token_b,
            all_markets_data
        ))

    async def get_market_ticks_liquidity(self, market_id) -> list: # noqa
        try:
            return await func_call(HAIKO_MARKET_MANAGER_ADDRESS, "depth", [market_id])
        except Exception as e:
            print(f"Failed for market ID: {market_id}")  # TODO: add resolve for contract fail
            return []

    def set_current_price(self, current_tick: Decimal) -> None:
        """
        Set the current price based on the current tick.
        :param current_tick: Int - Current tick
        """
        self.tick_current_price = self.tick_to_price(current_tick)

    def sort_asks_bids(self):
        pass

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
            market_ticks_liquidity = await self.get_market_ticks_liquidity(market_id)
            if not market_ticks_liquidity:
                continue
            self._calculate_order_book(market_ticks_liquidity, liquidity, market["currLimit"])

    def _calculate_order_book(
            self,
            market_ticks_liquidity: list,
            liquidity: Decimal,
            current_tick: Decimal
    ) -> None:
        self.set_current_price(current_tick)
        min_price, max_price = self.calculate_price_range()
        items_in_group = (len(market_ticks_liquidity) - 1) // market_ticks_liquidity[0]
        ticks_info = HaikoOrderBook.group_ticks_info(market_ticks_liquidity[1:], items_in_group)
        process_ticks = partial(self.process_ticks, liquidity, min_price, max_price)
        asks, bids = self.divide_ticks_on_bids_asks(ticks_info)
        process_ticks(asks, is_ask=True)
        process_ticks(bids, is_ask=False)

    def process_ticks(
            self,
            market_liquidity: Decimal,
            min_price: Decimal,
            max_price: Decimal,
            ticks: tuple,
            is_ask=True
    ) -> None:
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
        current_price_formatted = self.tick_current_price * (10 ** self.token_a_decimal + self.token_b_decimal)
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
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2 ** 128))
        return liquidity_delta / 10 ** self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.00001") ** tick * (10 ** (self.token_a_decimal - self.token_b_decimal))

    @staticmethod
    def group_ticks_info(ticks_info, n, fillvalue=None):
        if n == 0:
            return 0
        if len(ticks_info) % n != 0:
            raise ValueError("Ticks info list should be dividable by n")
        args = [iter(ticks_info)] * n
        return zip_longest(*args, fillvalue=fillvalue)


if __name__ == '__main__':
    token_0 = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_1 = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    order_book = HaikoOrderBook(token_0, token_1)
    print(order_book.tick_to_price(Decimal(-1963856)))
    # order_book.fetch_price_and_liquidity()
    res = asyncio.run(
        order_book.get_market_ticks_liquidity("0x3c62f0152e3b7fdc0144c7a06af97e2e007008d67321074fc336798975ecbeb")
    )
    res = list(HaikoOrderBook.group_ticks_info(res[1:], 5))
    # print((Decimal("1.00001") ** 5953400) * 10 ** 12)
    # print(Decimal(0.0003911729500584983))
    # print(Decimal(3911729500584983102980878) / (10 ** 28))
    print(Decimal(28773339936904503489).sqrt() / 10**18)
    print(Decimal(34105150426706005793))
    print(Decimal(5942350) - Decimal(7906205))
