from decimal import Decimal
from abc import ABC, abstractmethod

from web_app.order_books.constants import TOKEN_MAPPING


class OrderBookBase(ABC):
    DEX: str = None
    MIN_PRICE_RANGE = Decimal("0.1")
    MAX_PRICE_RANGE = Decimal("1.90")

    def __init__(self, token_a: str, token_b: str):
        self.token_a = token_a
        self.token_b = token_b
        self.asks = []  # List of tuples (price, quantity)
        self.bids = []  # List of tuples (price, quantity)
        self.timestamp = None
        self.block = None
        self.current_price = Decimal("0")
        self.token_a_decimal = TOKEN_MAPPING.get(token_a).decimals
        self.token_b_decimal = TOKEN_MAPPING.get(token_b).decimals
        self.total_liquidity = Decimal("0")

    @abstractmethod
    def fetch_price_and_liquidity(self) -> None:
        """
        Fetches the price and liquidity data from the connector
        """
        pass

    @abstractmethod
    def _calculate_order_book(self, *args, **kwargs) -> tuple:
        """
        Calculates order book data based on the liquidity data
        """
        pass

    def calculate_price_range(self) -> tuple:
        """
        Calculate the minimum and maximum price based on the current price.
        :return: tuple - The minimum and maximum price range.
        """
        min_price = self.current_price * self.MIN_PRICE_RANGE
        max_price = self.current_price * self.MAX_PRICE_RANGE
        return min_price, max_price

    @abstractmethod
    def calculate_liquidity_amount(self, *args, **kwargs) -> Decimal:
        """
        Calculates the liquidity amount based on the liquidity delta difference
        """
        pass

    @staticmethod
    def get_sqrt_ratio(tick: Decimal) -> Decimal:
        """
        Get the square root ratio based on the tick.
        :param tick: tick value
        :return: square root ratio
        """
        return (Decimal("1.000001").sqrt() ** tick) * (Decimal(2) ** 128)

    @abstractmethod
    def tick_to_price(self, tick: Decimal) -> Decimal:
        """
        Converts the tick value to price
        """
        pass

    def get_order_book(self) -> dict:
        """
        Returns the order book data
        :return: dict - The order book data
        """
        return {
            "token_a": self.token_a,
            "token_b": self.token_b,
            "timestamp": self.timestamp,
            "block": self.block,
            "dex": self.DEX,
            "asks": sorted(self.asks, key=lambda x: x[0]),
            "bids": sorted(self.bids, key=lambda x: x[0]),
        }

