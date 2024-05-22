from decimal import Decimal, getcontext
import pandas as pd
from dataclasses import dataclass
from web_app.ekubo.api_connector import EkuboAPIConnector

getcontext().prec = 18


@dataclass
class TokenConfig:
    name: str
    decimals: int


TOKEN_MAPPING = {
    "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": TokenConfig(
        name="ETH", decimals=18
    ),
    "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": TokenConfig(
        name="USDC", decimals=6
    ),
    "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21": TokenConfig(
        name="USDT", decimals=6
    ),
    "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f": TokenConfig(
        name="DAI", decimals=18
    ),
    "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef": TokenConfig(
        name="wBTC", decimals=8
    ),
    "0x07514ee6fa12f300ce293c60d60ecce0704314defdb137301dae78a7e5abbdd7": TokenConfig(
        name="STRK", decimals=18
    ),
    # FIXME: Placeholder address
    "0x0000000000000000000000000000000000000000000000000000000000000000": TokenConfig(
        name="UNO", decimals=18
    ),
    # FIXME: Placeholder address
    "0x0000000000000000000000000000000000000000000000000000000000000001": TokenConfig(
        name="ZEND", decimals=18
    ),
    # FIXME: Placeholder address
    "0x0000000000000000000000000000000000000000000000000000000000000002": TokenConfig(
        name="wstETH", decimals=18
    ),
    # FIXME: Placeholder address
    "0x0000000000000000000000000000000000000000000000000000000000000003": TokenConfig(
        name="LORDS", decimals=18
    ),
}


class EkuboOrderBook:
    def __init__(self, token_a: str, token_b: str, dex: str):
        self.token_a = token_a
        self.token_b = token_b
        self.dex = dex
        self.asks = []  # List of tuples (price, quantity)
        self.bids = []  # List of tuples (price, quantity)
        self.timestamp = None
        self.block = None
        self.token_a_decimal = TOKEN_MAPPING.get(token_a).decimals
        self.token_b_decimal = TOKEN_MAPPING.get(token_b).decimals
        self.total_liquidity = Decimal("0")

    def fetch_price_and_liquidity(self) -> None:
        """
        Fetch the current price and liquidity of the pair from the Ekubo API.
        """
        connector = EkuboAPIConnector()

        # Get current price
        price_data = connector.get_pair_price(self.token_a, self.token_b)
        current_price = Decimal(price_data.get("price", "0"))
        self.current_price = current_price
        self.timestamp = price_data["timestamp"]

        # Get pool liquidity
        pools = connector.get_pools()
        df = pd.DataFrame(pools)
        pool_df = df.loc[
            (df["token0"] == self.token_a) & (df["token1"] == self.token_b)
        ]
        for index, row in pool_df.iterrows():
            key_hash = row["key_hash"]
            sqrt_ratio = self.hex_to_decimal(row["sqrt_ratio"])
            # Fetch pool liquidity data
            liquidity_data = connector.get_pool_liquidity(key_hash)
            self.block = row["lastUpdate"]["event_id"]
            self._calculate_order_book(
                liquidity_data["data"], current_price, sqrt_ratio
            )

    def calculate_price_range(self, current_price: Decimal) -> tuple:
        """
        Calculate the minimum and maximum price based on the current price.
        :param current_price: Current price of the pair.
        :return: tuple - The minimum and maximum price range.
        """
        min_price = current_price * Decimal("0.95")
        max_price = current_price * Decimal("1.05")
        return min_price, max_price

    def _calculate_order_book(self, liquidity_data, current_price, sqrt_ratio):
        min_price, max_price = self.calculate_price_range(current_price)

        for data in liquidity_data:
            tick = Decimal(data["tick"])
            tick_price = self.tick_to_price(tick)
            effective_price = current_price + tick_price

            if min_price <= effective_price <= max_price:
                liquidity_delta_diff = Decimal(data["net_liquidity_delta_diff"])

                self.total_liquidity += liquidity_delta_diff

                if tick > 0:
                    self.asks.append(
                        (effective_price, liquidity_delta_diff * sqrt_ratio)
                    )
                else:
                    self.bids.append(
                        (effective_price, liquidity_delta_diff * sqrt_ratio)
                    )

    def tick_to_price(self, tick: Decimal) -> Decimal:
        """
        Convert a tick to the corresponding price using the Uniswap V3 formula.

        :param tick: Decimal - The tick value to convert to a price.
        :return: Decimal - The price corresponding to the given tick.
        """
        # Calculate the price from the tick using the Uniswap V3 formula
        multiply_factor = self.token_b_decimal - self.token_a_decimal
        adjustment_factor = Decimal("10") ** Decimal(multiply_factor)
        tick_value = Decimal("1.0001") ** (tick * adjustment_factor)
        return tick_value

    # TODO alternative to calculate price from tick
    # def tick_to_price(self, tick: int, sqrt_ratio_test) -> Decimal:
    #     sqrt_ratio = (Decimal('1.000001').sqrt() ** tick) * (Decimal(2) ** 128)
    #     price = sqrt_ratio ** 2 / (Decimal(2) ** 256)
    #     return price

    def hex_to_decimal(self, hex_str: str) -> Decimal:
        """
        Convert a hex string to a decimal number.
        :param hex_str: str - The hex string to convert.
        :return: Decimal - The decimal number corresponding to the hex string.
        """
        # Convert hex sqrtPriceX96 to decimal
        return Decimal(int(hex_str, 16)) / (Decimal(2) ** 96)

    def get_order_book(self) -> dict:
        return {
            "token_a": self.token_a,
            "token_b": self.token_b,
            "timestamp": self.timestamp,
            "block": self.block,
            "dex": self.dex,
            "asks": self.asks,
            "bids": self.bids,
        }


if __name__ == "__main__":
    # FIXME this code is not production, it's for testing purpose only
    eth_decimals = 18
    usdc_decimals = 6
    token_a = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_b = (
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    )

    pool_states = EkuboAPIConnector().get_pools()
    order_book = EkuboOrderBook(token_a, token_b, "Ekubo")
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n")
