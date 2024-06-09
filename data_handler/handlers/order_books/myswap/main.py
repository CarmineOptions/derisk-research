import asyncio
import math
from decimal import Decimal

from handlers.blockchain_call import func_call
from handlers.order_books.abstractions import OrderBookBase

import pandas as pd

from handlers.order_books.myswap.api_connection.api_connector import MySwapAPIConnector
from handlers.order_books.myswap.api_connection.data_collectors import braavos_get_tokens_prices


MYSWAP_CL_MM_ADDRESS = "0x01114c7103e12c2b2ecbd3a2472ba9c48ddcbf702b1c242dd570057e26212111"
MAX_MYSWAP_TICK = Decimal("1774532")


class MySwapOrderBook(OrderBookBase):
    DEX = "MySwap"
    MIN_PRICE_RANGE = Decimal("0.1")
    MAX_PRICE_RANGE = Decimal("1.3")

    def __init__(self, token_a: str, token_b: str, apply_filtering: bool = False):
        # TODO: Add logging
        super().__init__(token_a, token_b)
        self.token_a_name = None
        self.token_b_name = None
        self.connector = MySwapAPIConnector()
        self.apply_filtering = apply_filtering
        self._usd_price = Decimal("0")
        self._decimals_diff = Decimal(10 ** (self.token_a_decimal - self.token_b_decimal))
        self._set_token_names()
        self._set_usd_price()

    def _set_token_names(self):
        token_a_info, token_b_info = self.get_tokens_configs()
        self.token_a_name = token_a_info.name
        self.token_b_name = token_b_info.name

    def _read_liquidity_data(self, pool_id: str) -> pd.DataFrame:
        """
        Read liquidity data from the MySwap data service.
        :param pool_id: str - The pool id in hexadecimal.
        :return: pd.DataFrame - The liquidity data.
        The structure of the data:
        Columns: tick(numpy.int64), liq(numpy.int64)
        """
        url = f"https://myswap-cl-charts.s3.amazonaws.com/data/pools/{pool_id}/liqmap.json.gz"
        return pd.read_json(url, compression="gzip")

    async def _async_fetch_price_and_liquidity(self) -> None:
        all_pools = self.connector.get_pools_data()
        filtered_pools = self._filter_pools_data(all_pools)
        for pool in filtered_pools:
            await self._calculate_order_book(pool["poolkey"])

    def fetch_price_and_liquidity(self) -> None:
        # TODO: Create new event loop if not running
        asyncio.run(self._async_fetch_price_and_liquidity())

    def _set_usd_price(self):
        if not self.token_a_name:
            raise ValueError("Base token name is not defined.")
        token_info = braavos_get_tokens_prices([self.token_a_name.lower()])
        if not token_info or isinstance(token_info, dict):
            raise RuntimeError(f"Couldn't get token usd price: {token_info.get('error', 'Unknown error')}")
        self._usd_price = Decimal(token_info[0]["price"])

    def _filter_pools_data(self, all_pools: dict) -> list:
        """
        Filter pools data based on the token pair.
        :param all_pools: dict - All pools data.
        :return: list - Pools for current pair.
        """
        return list(filter(
            lambda pool: pool["token0"]["address"] == self.token_a and pool["token1"]["address"] == self.token_b,
            all_pools["pools"]
        ))

    def _get_ticks_range(self) -> tuple[Decimal, Decimal]:
        """
        Get ticks range based on the current price range.
        return: tuple[Decimal, Decimal] - The minimum and maximum ticks.
        """
        price_range = self.calculate_price_range()
        return self._price_to_tick(price_range[0]), self._price_to_tick(price_range[1])

    def _price_to_tick(self, price: Decimal) -> Decimal:
        """
        Convert price to MySwap tick.
        :param price: Decimal - The price to convert.
        :return: Decimal - The unsigned tick value.
        Signed tick calculation formula:
        round(log(price / (2 ** 128 * decimals_diff)) / log(1.0001))
        """
        signed_tick = round(
            Decimal(math.log(
                price / (Decimal(2 ** 128) * self._decimals_diff))
            ) / Decimal(math.log(Decimal("1.0001")))
        )
        return Decimal(signed_tick) + MAX_MYSWAP_TICK

    async def _calculate_order_book(self, pool_id: str) -> None:
        # Obtain liquidity data and tick
        data = self._read_liquidity_data(pool_id)
        if data.empty:
            return
        current_tick = await func_call(MYSWAP_CL_MM_ADDRESS, "current_tick", [pool_id])
        if not current_tick:
            return
        current_tick = current_tick[0]

        # Set prices boundaries in ticks
        self.current_price = self.tick_to_price(current_tick)
        min_tick, max_tick = self._get_ticks_range()

        # Prepare data for processing
        data = data.loc[(min_tick < data["tick"]) & (data["tick"] <= max_tick)]
        asks, bids = data[data["tick"] >= current_tick], data[data["tick"] < current_tick]
        bids = bids.sort_values("tick", ascending=True)

        # Add asks and bids to the order book
        self.add_bids(bids, (min_tick, max_tick))
        self.add_asks(asks, bids.iloc[0]["liq"], (min_tick, max_tick))
        tvl = (
                (sum([bid[1] for bid in self.bids]) * self._usd_price) +
                (sum([ask[1] for ask in self.asks]) * self._usd_price)
        )

    def add_asks(self, pool_asks: pd.DataFrame, pool_liquidity: Decimal, price_range: tuple[Decimal, Decimal]) -> None:
        if pool_asks.empty:
            return
        local_asks = []
        prev_tick = Decimal(pool_asks.iloc[0]['tick'].item())
        prev_price = self.tick_to_price(prev_tick)
        y = self._get_token_amount(
            pool_liquidity,
            self.current_price.sqrt(),
            prev_price.sqrt(),
            is_ask=False
        )
        local_asks.append((prev_price, y))
        for index, bid_info in enumerate(pool_asks.iloc[::-1].itertuples(index=False)):
            if index == 0:
                continue
            current_tick = Decimal(pool_asks.iloc[index - 1]['tick'].item())
            current_price = self.tick_to_price(current_tick)
            y = self._get_token_amount(
                Decimal(pool_asks.iloc[index - 1]['liq'].item()),
                current_price.sqrt(),
                Decimal(self.tick_to_price(pool_asks.iloc[index]['tick'].item())).sqrt(),
                is_ask=False
            )
            local_asks.append((current_price, y))
        if self.apply_filtering:
            self.bids.extend([bid for bid in local_asks if price_range[0] < bid[0] < price_range[1]])
            return
        self.asks.extend(local_asks)

    def add_bids(self, pool_bids: pd.DataFrame, price_range: tuple[Decimal, Decimal]) -> None:
        if pool_bids.empty:
            return
        local_bids = []
        prev_tick = Decimal(pool_bids.iloc[0]['tick'].item())
        prev_price = self.tick_to_price(prev_tick)
        y = self._get_token_amount(
            Decimal(pool_bids.iloc[0]['liq'].item()),
            self.current_price.sqrt(),
            prev_price.sqrt(),
            is_ask=False
        )
        local_bids.append((prev_price, y))
        for index, bid_info in enumerate(pool_bids.iloc[::-1].itertuples(index=False)):
            if index == 0:
                continue
            current_tick = Decimal(pool_bids.iloc[index - 1]['tick'].item())
            current_price = self.tick_to_price(current_tick)
            y = self._get_token_amount(
                Decimal(pool_bids.iloc[index]['liq'].item()),
                current_price.sqrt(),
                Decimal(self.tick_to_price(pool_bids.iloc[index]['tick'].item())).sqrt(),
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
        :return: Decimal - token amount
        """
        if is_ask and (current_sqrt == 0 or next_sqrt == 0):
            raise ValueError("Square root of prices for asks can't be zero.")
        if not is_ask and next_sqrt == 0:
            return abs(current_liq / current_sqrt) / self._decimals_diff
        amount = abs(current_liq / next_sqrt - current_liq / current_sqrt)
        return amount / self._decimals_diff

    def tick_to_price(self, tick: Decimal) -> Decimal:
        return Decimal("1.0001") ** (tick - MAX_MYSWAP_TICK) * Decimal(2 ** 128) * self._decimals_diff

    def calculate_liquidity_amount(self, tick, liquidity_pair_total) -> Decimal:
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2 ** 128))
        return liquidity_delta / 10 ** self.token_a_decimal


if __name__ == '__main__':
    order_book = MySwapOrderBook(
        "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
    )
    order_book.fetch_price_and_liquidity()
