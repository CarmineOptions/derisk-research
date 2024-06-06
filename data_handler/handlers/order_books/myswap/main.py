import asyncio
import math
from decimal import Decimal

from handlers.blockchain_call import func_call
from handlers.order_books.abstractions import OrderBookBase

import pandas as pd

from handlers.order_books.myswap.api_connector import MySwapAPIConnector


MYSWAP_CL_MM_ADDRESS = "0x01114c7103e12c2b2ecbd3a2472ba9c48ddcbf702b1c242dd570057e26212111"


class MySwapOrderBook(OrderBookBase):
    DEX = "MySwap"

    def __init__(self, token_a: str, token_b: str):
        super().__init__(token_a, token_b)
        self.connector = MySwapAPIConnector()

    def _read_liquidity_data(self, pool_id: str) -> pd.DataFrame:
        url = f"https://myswap-cl-charts.s3.amazonaws.com/data/pools/{pool_id}/liqmap.json.gz"
        return pd.read_json(url, compression="gzip")

    async def _async_fetch_price_and_liquidity(self) -> None:
        all_pools = self.connector.get_pools_data()
        filtered_pools = self._filter_pools_data(all_pools)
        for pool in filtered_pools:
            await self._calculate_order_book(pool["poolkey"])

    def fetch_price_and_liquidity(self) -> None:
        asyncio.run(self._async_fetch_price_and_liquidity())

    def _filter_pools_data(self, all_pools: dict) -> list:
        return list(filter(
            lambda pool: pool["token0"]["address"] == self.token_a and pool["token1"]["address"] == self.token_b,
            all_pools["pools"]
        ))

    async def _calculate_order_book(self, pool_id: str) -> None:
        data = self._read_liquidity_data(pool_id)
        current_tick = await func_call(MYSWAP_CL_MM_ADDRESS, "current_tick", [pool_id])
        data_filtered = data.loc[data["liq"] > 0]

    def calculate_price_range(self) -> tuple:
        pass

    def tick_to_price(self, tick: Decimal) -> Decimal:
        pass

    def calculate_liquidity_amount(self, *args, **kwargs) -> Decimal:
        pass


if __name__ == '__main__':
    order_book = MySwapOrderBook(
        "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
    )
    order_book.fetch_price_and_liquidity()
    # Get price from sqrt price
    sqrt_price = 4888134925013110180250533
    print((Decimal(sqrt_price) / Decimal(2**96)) ** Decimal(2) * Decimal(10 ** 12))

    # Get price from tick
    MAX_TICK = 1774532
    # Possible formula:
    price = Decimal("1.0001") ** Decimal(693396 - MAX_TICK) * Decimal(2 ** 128) * Decimal(10 ** 12)
    print(price)
