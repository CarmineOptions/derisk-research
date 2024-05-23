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
    "0x0719b5092403233201aa822ce928bd4b551d0cdb071a724edd7dc5e5f57b7f34": TokenConfig(
        name="UNO", decimals=18
    ),
    "0x00585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34": TokenConfig(
        name="ZEND", decimals=18
    ),
    "0x07e2c010c0b381f347926d5a203da0335ef17aefee75a89292ef2b0f94924864": TokenConfig(
        name="wstETH", decimals=18
    ),
    "0x4c4fb1ab068f6039d5780c68dd0fa2f8742cceb3426d19667778ca7f3518a9": TokenConfig(
        name="LORDS", decimals=18
    ),
}


class EkuboOrderBook:
    def __init__(self, token_a: str, token_b: str, dex: str):
        """
        Initialize the EkuboOrderBook object.
        :param token_a: BaseToken contract address
        :param token_b: QuoteToken contract address
        :param dex: The DEX name
        """
        self.token_a = token_a
        self.token_b = token_b
        self.dex = dex
        self.asks = []  # List of tuples (price, quantity)
        self.bids = []  # List of tuples (price, quantity)
        self.timestamp = None
        self.block = None
        self.current_price = 0
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
            self.total_liquidity = int(row["liquidity"])
            liquidity_data = connector.get_pool_liquidity(key_hash)
            self.block = row["lastUpdate"]["event_id"]
            self._calculate_order_book(
                liquidity_data["data"], current_price, sqrt_ratio
            )

    @staticmethod
    def calculate_price_range(current_price: Decimal) -> tuple:
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
            # calculate price based on tick
            tick_price = self.tick_to_price(tick)
            if min_price <= tick_price <= max_price:
                liquidity_delta_diff = Decimal(data["net_liquidity_delta_diff"])
                # update total liquidity
                self.total_liquidity += liquidity_delta_diff
                # update order book

                liquidity_amount = self.calculate_liquidity_amount(sqrt_ratio)
                if tick_price > current_price:
                    self.asks.append((tick_price, liquidity_amount))
                else:
                    self.bids.append((tick_price, liquidity_amount))

    def calculate_liquidity_amount(self, sqrt_ratio: Decimal) -> Decimal:
        """
        Calculate the liquidity amount based on the liquidity delta and sqrt ratio.
        :param sqrt_ratio: Decimal - The sqrt ratio.
        :return: Decimal - The liquidity amount.
        """
        liquidity_delta = self.total_liquidity / sqrt_ratio
        liquidity_amount = liquidity_delta / Decimal('10') ** self.token_a_decimal
        return liquidity_amount

    def tick_to_price(self, tick: Decimal) -> Decimal:
        """
        Convert tick to price.
        :param tick: tick value
        :return: price by tick
        """
        # calculate sqrt ratio by formula sqrt_ratio = (1.000001 ** tick) * (2 ** 128)
        sqrt_ratio = (Decimal('1.000001').sqrt() ** tick) * (Decimal(2) ** 128)
        # calculate price by formula price = (sqrt_ratio / (2 ** 128)) ** 2 * 10 ** (token_a_decimal - token_b_decimal)
        price = ((sqrt_ratio / (Decimal(2) ** 128)) ** 2) * 10 ** (self.token_a_decimal - self.token_b_decimal)
        return price

    @staticmethod
    def hex_to_decimal(hex_str: str) -> Decimal:
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
            "asks": sorted(self.asks, key=lambda x: x[0]),
            "bids": sorted(self.bids, key=lambda x: x[0]),
        }

    def calculate_price_change(self, sell_amount: Decimal) -> tuple:
        remaining_sell_amount = sell_amount
        total_cost = Decimal("0")
        total_tokens = Decimal("0")

        for price, quantity in sorted(self.bids, key=lambda x: x[0], reverse=True):
            if remaining_sell_amount <= quantity:
                total_cost += remaining_sell_amount * price
                total_tokens += remaining_sell_amount
                break
            else:
                total_cost += quantity * price
                total_tokens += quantity
                remaining_sell_amount -= quantity

        new_price = price if remaining_sell_amount <= quantity else (self.bids[-1][0] if self.bids else Decimal("0"))
        average_price = total_cost / total_tokens if total_tokens != 0 else Decimal("0")

        return new_price, average_price


if __name__ == "__main__":
    # FIXME this code is not production, it's for testing purpose only
    token_a = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_b = (
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    )
    pool_states = EkuboAPIConnector().get_pools()
    order_book = EkuboOrderBook(token_a, token_b, "Ekubo")
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n") # FIXME remove debug print
    print(f"Price change: {order_book.calculate_price_change(Decimal('1000'))}, current price: {order_book.current_price}") # FIXME remove debug print
