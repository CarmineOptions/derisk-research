""" This module contains the EkuboOrderBook class. """
from decimal import Decimal, getcontext

import pandas as pd
from data_handler.handlers.order_books.abstractions import OrderBookBase
from data_handler.handlers.order_books.ekubo.api_connector import EkuboAPIConnector

getcontext().prec = 18


class EkuboOrderBook(OrderBookBase):
    """ Ekubo Order Book class. """
    DEX = "Ekubo"

    def __init__(self, token_a: str, token_b: str) -> None:
        """
        Initialize the EkuboOrderBook object.
        :param token_a: BaseToken contract address
        :param token_b: QuoteToken contract address
        """
        super().__init__(token_a, token_b)
        self.connector = EkuboAPIConnector()

    def set_current_price(self) -> str:
        """
        Get the current price of the pair.
        :return: str - The current price of the pair.
        """
        price_data = self.connector.get_pair_price(self.token_a, self.token_b)
        self.current_price = Decimal(price_data.get("price", "0"))

    def fetch_price_and_liquidity(self) -> None:
        """
        Fetch the current price and liquidity of the pair from the Ekubo API.
        """
        # Get pool liquidity
        pools = self.connector.get_pools()
        df = pd.DataFrame(pools)
        # filter pool data by token_a and token_b
        pool_df = df.loc[(df["token0"] == self.token_a) & (df["token1"] == self.token_b)]

        # set current price
        self.set_current_price()
        for index, row in list(pool_df.iterrows()):
            key_hash = row["key_hash"]
            # Fetch pool liquidity data
            pool_liquidity = int(row["liquidity"])
            self.block = row["lastUpdate"]["event_id"]

            liquidity_response = self.connector.get_pool_liquidity(key_hash)
            liquidity_data = liquidity_response["data"]
            liquidity_data = sorted(liquidity_data, key=lambda x: x["tick"])

            self._calculate_order_book(
                liquidity_data,
                pool_liquidity,
                row,
            )

    def _calculate_order_book(
        self,
        liquidity_data: list,
        pool_liquidity: int,
        row: pd.Series,
    ) -> None:
        """
        Calculate the order book based on the liquidity data.
        :param liquidity_data: list - List of liquidity data
        :param pool_liquidity: pool liquidity
        :param row: pd.Series - Pool data
        """
        min_price, max_price = self.calculate_price_range()
        if not liquidity_data:
            return

        self.add_asks(liquidity_data, row)
        self.add_bids(liquidity_data, row)

        # Filter asks and bids by price range
        self.asks = [
            (price, supply) for price, supply in self.asks if min_price < price < max_price
        ]
        self.bids = [
            (price, supply) for price, supply in self.bids if min_price < price < max_price
        ]

    def add_asks(self, liquidity_data: list[dict], row: pd.Series) -> None:
        """
        Add `asks` to the order book.
        :param liquidity_data: list of dict with tick and net_liquidity_delta_diff
        :param row: pool row data
        """
        ask_ticks = [i for i in liquidity_data if i["tick"] >= row["tick"]]
        if not ask_ticks:
            return

        glob_liq = Decimal(row["liquidity"])

        # Calculate for current tick (loops start with the next one)
        next_tick = ask_ticks[0]["tick"]
        prev_tick = next_tick - row["tick_spacing"]

        prev_sqrt = self._get_pure_sqrt_ratio(prev_tick)
        next_sqrt = self._get_pure_sqrt_ratio(next_tick)

        supply = abs(((glob_liq / prev_sqrt) - (glob_liq / next_sqrt)) / 10**self.token_a_decimal)
        price = self.tick_to_price(prev_tick)
        self.asks.append((price, supply))

        for index, tick in enumerate(ask_ticks):
            if index == 0:
                continue
            glob_liq += Decimal(ask_ticks[index - 1]["net_liquidity_delta_diff"])
            prev_tick = Decimal(ask_ticks[index - 1]["tick"])

            curr_tick = Decimal(tick["tick"])

            prev_sqrt = self._get_pure_sqrt_ratio(prev_tick)
            next_sqrt = self._get_pure_sqrt_ratio(curr_tick)

            supply = abs(
                ((glob_liq / prev_sqrt) - (glob_liq / next_sqrt)) / 10**self.token_a_decimal
            )
            price = self.tick_to_price(prev_tick)
            self.asks.append((price, supply))

    def add_bids(self, liquidity_data: list[dict], row: pd.Series) -> None:
        """
        Add `bids` to the order book.
        :param liquidity_data: liquidity data list of dict with tick and net_liquidity_delta_diff
        :param row: pool row data
        """
        bid_ticks = [i for i in liquidity_data if i["tick"] <= row["tick"]][::-1]
        if not bid_ticks:
            return

        glob_liq = Decimal(row["liquidity"])

        next_tick = bid_ticks[0]["tick"]
        prev_tick = next_tick + row["tick_spacing"]

        prev_sqrt = self._get_pure_sqrt_ratio(prev_tick)
        next_sqrt = self._get_pure_sqrt_ratio(next_tick)

        supply = abs(((glob_liq * prev_sqrt) - (glob_liq * next_sqrt)) / 10**self.token_b_decimal)
        price = self.tick_to_price(prev_tick)
        self.bids.append((price, supply))

        for index, tick in enumerate(bid_ticks):
            if index == 0:
                continue
            glob_liq -= Decimal(bid_ticks[index - 1]["net_liquidity_delta_diff"])
            prev_tick = Decimal(bid_ticks[index - 1]["tick"])
            curr_tick = Decimal(tick["tick"])

            prev_sqrt = self._get_pure_sqrt_ratio(prev_tick)
            next_sqrt = self._get_pure_sqrt_ratio(curr_tick)

            supply = (
                abs(((glob_liq * prev_sqrt) - (glob_liq * next_sqrt))) / 10**self.token_b_decimal
            )
            price = self.tick_to_price(prev_tick)
            self.bids.append((price, supply))

    def _get_pure_sqrt_ratio(self, tick: Decimal) -> Decimal:
        """
        Get the square root ratio based on the tick.
        :param tick: tick value
        :return: square root ratio
        """
        return Decimal("1.000001").sqrt()**tick

    @staticmethod
    def sort_ticks_by_asks_and_bids(sorted_liquidity_data: list,
                                    current_tick: int) -> tuple[list, list]:
        """
        Sort tick by ask and bid
        :param sorted_liquidity_data: list - List of sorted liquidity data
        :param current_tick: int - Current tick
        :return: list - List of sorted liquidity data
        """
        sorted_liquidity_data = sorted(sorted_liquidity_data, key=lambda x: x["tick"])
        ask_data, bid_data = [], []
        for sorted_data in sorted_liquidity_data:
            if sorted_data["tick"] > current_tick:
                ask_data.append(sorted_data)
            else:
                bid_data.append(sorted_data)
        return ask_data, bid_data

    def calculate_liquidity_amount(self, tick: Decimal, liquidity_pair_total: Decimal) -> Decimal:
        """
        Calculate the liquidity amount based on the liquidity delta and sqrt ratio.
        :param tick: Decimal - The sqrt ratio.
        :param liquidity_pair_total: Decimal - The liquidity pair total.
        :return: Decimal - The liquidity amount.
        """
        sqrt_ratio = self.get_sqrt_ratio(tick)
        liquidity_delta = liquidity_pair_total / (sqrt_ratio / Decimal(2**128))
        return liquidity_delta / 10**self.token_a_decimal

    def tick_to_price(self, tick: Decimal) -> Decimal:
        """
        Convert tick to price.
        :param tick: tick value
        :return: price by tick
        """
        sqrt_ratio = self.get_sqrt_ratio(tick)
        # calculate price by formula price = (sqrt_ratio / (2 ** 128)) ** 2 * 10
        # ** (token_a_decimal - token_b_decimal)
        price = ((sqrt_ratio /
                  (Decimal(2)**128))**2) * 10**(self.token_a_decimal - self.token_b_decimal)
        return price


def debug_code() -> None:
    """
    This function is used to test the EkuboOrderBook class.
    """
    token_a = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"  # ETH
    token_b = (
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"  # USDC
    )
    order_book = EkuboOrderBook(token_a, token_b)
    order_book.fetch_price_and_liquidity()
    print(order_book.get_order_book(), "\n")
