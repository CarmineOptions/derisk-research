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
    DEX = "Ekubo"
    MIN_PRICE_RANGE = Decimal("0.1")
    MAX_PRICE_RANGE = Decimal("1.90")

    def __init__(self, token_a: str, token_b: str):
        """
        Initialize the EkuboOrderBook object.
        :param token_a: BaseToken contract address
        :param token_b: QuoteToken contract address
        :param dex: The DEX name
        """
        self.token_a = token_a
        self.token_b = token_b
        self.asks = []  # List of tuples (price, quantity)
        self.bids = []  # List of tuples (price, quantity)
        self.timestamp = None
        self.block = None
        self.current_price = 0
        self.token_a_decimal = TOKEN_MAPPING.get(token_a).decimals
        self.token_b_decimal = TOKEN_MAPPING.get(token_b).decimals
        self.total_liquidity = Decimal("0")
        self.connector = EkuboAPIConnector()

    def fetch_price_and_liquidity(self) -> None:
        """
        Fetch the current price and liquidity of the pair from the Ekubo API.
        """
        # Get pool liquidity
        pools = self.connector.get_pools()
        df = pd.DataFrame(pools)
        pool_df = df.loc[
            (df["token0"] == self.token_a) & (df["token1"] == self.token_b)
        ]

        for index, row in list(pool_df.iterrows())[:1]:
        # for index, row in pool_df.iterrows():
            key_hash = row["key_hash"]
            sqrt_ratio = int(row["sqrt_ratio"], base=16)
            # Fetch pool liquidity data
            pool_liquidity = int(row["liquidity"])
            liquidity_data = self.connector.get_pool_liquidity(key_hash)
            self.block = row["lastUpdate"]["event_id"]
            self._calculate_order_book(
                liquidity_data["data"], 
                sqrt_ratio, 
                pool_liquidity,
                row['tick'] # This is the current tick = current price
            )

    def sort_ticks_by_asks_and_bids(self, sorted_liquidity_data: list, current_tick: int) -> tuple[list, list]:
        """
        Sort tick by ask and bid
        :param sorted_liquidity_data: list - List of sorted liquidity data
        :return: list - List of sorted liquidity data
        """
        sorted_liquidity_data = sorted(sorted_liquidity_data, key=lambda x: x["tick"])
        ask_data = []
        bid_data = []
        for sorted_data in sorted_liquidity_data:
            if sorted_data['tick'] > current_tick:
                ask_data.append(sorted_data)
            else:
                bid_data.append(sorted_data)
        return ask_data, bid_data

    def _calculate_order_book(self, liquidity_data, sqrt_ratio, pool_liquidity, current_tick):
        # Get current price
        self.set_current_price()
        min_price, max_price = self.calculate_price_range()

        sorted_liquidity_data = sorted(liquidity_data, key=lambda x: x["tick"])
        asks, bids = self.sort_ticks_by_asks_and_bids(sorted_liquidity_data, current_tick)

        ask_liquidity_pool = pool_liquidity
        for ask in asks:
            tick_price = self.tick_to_price(ask["tick"])

            liquidity_delta_diff = Decimal(ask["net_liquidity_delta_diff"])
            ask_liquidity_pool += liquidity_delta_diff
            
            liquidity_amount = self.calculate_liquidity_amount(sqrt_ratio, ask_liquidity_pool)
            self.asks.append((tick_price, liquidity_amount))

        bids_liquidity_pool = pool_liquidity
        for bid in bids[::-1]:
            tick_price = self.tick_to_price(bid["tick"])
            liquidity_delta_diff = Decimal(bid["net_liquidity_delta_diff"])
            bids_liquidity_pool += liquidity_delta_diff
            liquidity_amount = self.calculate_liquidity_amount(sqrt_ratio, bids_liquidity_pool)
            self.bids.append((tick_price, liquidity_amount))

    def calculate_price_range(self) -> tuple:
        """
        Calculate the minimum and maximum price based on the current price.
        :param current_price: Current price of the pair.
        :return: tuple - The minimum and maximum price range.
        """
        min_price = self.current_price * self.MIN_PRICE_RANGE
        max_price = self.current_price * self.MAX_PRICE_RANGE
        return min_price, max_price

    def set_current_price(self):
        price_data = self.connector.get_pair_price(self.token_a, self.token_b)
        current_price = Decimal(price_data.get("price", "0"))
        self.current_price = current_price
        self.timestamp = price_data["timestamp"]

    def calculate_liquidity_amount(self, sqrt_ratio: Decimal, liquidity_pair_total) -> Decimal:
        """
        Calculate the liquidity amount based on the liquidity delta and sqrt ratio.
        :param sqrt_ratio: Decimal - The sqrt ratio.
        :return: Decimal - The liquidity amount.
        """
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10**self.token_a_decimal

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

    def get_order_book(self) -> dict:
        return {
            "token_a": self.token_a,
            "token_b": self.token_b,
            "timestamp": self.timestamp,
            "block": self.block,
            "dex": self.DEX,
            "asks": sorted(self.asks, key=lambda x: x[0]),
            "bids": sorted(self.bids, key=lambda x: x[0]),
        }

    def calculate_price_change(self, sell_amount: Decimal) -> tuple:
        remaining_sell_amount = sell_amount
        total_cost = Decimal("0")
        total_tokens = Decimal("0")
        df = pd.DataFrame(sorted(self.bids, key=lambda x: x[0], reverse=True), columns=["price", "quantity"])
        df_filtered = df.loc[df["price"] < self.current_price]
        for price, quantity in df_filtered.itertuples(index=False):
            if remaining_sell_amount <= quantity:
                total_cost += remaining_sell_amount * price
                total_tokens += remaining_sell_amount
                break
            else:
                total_cost += quantity * price
                total_tokens += quantity
                remaining_sell_amount -= quantity

        average_price = total_cost / total_tokens if total_tokens != 0 else Decimal("0")

        return average_price


if __name__ == "__main__":
    # FIXME this code is not production, it's for testing purpose only
    token_a = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_b = (
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    )
    pool_states = EkuboAPIConnector().get_pools()
    order_book = EkuboOrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    r = order_book.get_order_book()
    print(order_book.get_order_book(), "\n") # FIXME remove debug print
    print(f"Avarage change: {order_book.calculate_price_change(Decimal('10'))}, current price: {order_book.current_price}") # FIXME remove debug print
