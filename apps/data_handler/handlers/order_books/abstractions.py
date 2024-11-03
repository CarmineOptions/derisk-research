""" Abstract base classes for order book data and API connectors. """
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal

import requests

from data_handler.db.schemas import OrderBookResponseModel

from .constants import TOKEN_MAPPING, TokenConfig


class OrderBookBase(ABC):
    """ Base class for order book data """
    DEX: str = None
    MIN_PRICE_RANGE = Decimal("0.0001")
    MAX_PRICE_RANGE = Decimal("100.0")

    def __init__(self, token_a: str, token_b: str):
        self.token_a = token_a
        self.token_b = token_b
        self.asks = []  # List of tuples (price, quantity)
        self.bids = []  # List of tuples (price, quantity)
        self.timestamp = None
        self.block = None
        self.current_price = Decimal("0")
        self.token_a_decimal = self.get_token_decimals(token_a)
        self.token_b_decimal = self.get_token_decimals(token_b)
        self.total_liquidity = Decimal("0")

    def get_token_configs(self) -> tuple[TokenConfig, TokenConfig]:
        """
        Method to get the token configurations
        :return: tuple[TokenConfig, TokenConfig] - The token configurations
        """
        token_a_info = TOKEN_MAPPING.get(self.token_a)
        token_b_info = TOKEN_MAPPING.get(self.token_b)
        if not token_a_info or not token_b_info:
            raise ValueError("Information about tokens isn't available.")
        return token_a_info, token_b_info

    def get_token_decimals(self, token: str) -> Decimal:
        """
        Get the token decimals
        :return: tuple - The token decimals
        """
        token_config = TOKEN_MAPPING.get(token)
        if token_config:
            return token_config.decimals
        return Decimal("0")

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
        return (Decimal("1.000001").sqrt()**tick) * (Decimal(2)**128)

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
        dt_now = datetime.now(timezone.utc)

        return {
            "token_a": self.token_a,
            "token_b": self.token_b,
            "timestamp": int(dt_now.replace(tzinfo=timezone.utc).timestamp()),
            "block": self.block,
            "dex": self.DEX,
            "current_price": self.current_price,
            "asks": sorted(self.asks, key=lambda x: x[0]),
            "bids": sorted(self.bids, key=lambda x: x[0]),
        }

    def serialize(self) -> OrderBookResponseModel:
        """
        Serialize the order book data
        :return: dict - The serialized order book data
        """
        order_book_data = self.get_order_book()
        return OrderBookResponseModel(**order_book_data)


class AbstractionAPIConnector(ABC):
    """
    Abstract base class for making HTTP GET and POST requests using the `requests` library.
    """

    API_URL: str = None

    @classmethod
    def send_get_request(cls, endpoint: str, params=None) -> dict:
        """
        Send a GET request to the specified endpoint with optional parameters.

        :param endpoint: The endpoint URL where the GET request will be sent.
        :type endpoint: str
        :param params: Dictionary of URL parameters to append to the URL.
        :type params: dict, optional
        :return: A JSON response from the API if the request is successful; 
        otherwise, a dictionary with an "error" key
        containing the error message.
        :rtype: dict
        """
        try:
            response = requests.get(f"{cls.API_URL}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    @classmethod
    def send_post_request(cls, endpoint: str, data=None, json=None) -> dict:
        """
        Send a POST request to the specified endpoint with either form data or a JSON payload.

        :param endpoint: The endpoint URL where the POST request will be sent.
        :type endpoint: str
        :param data: Dictionary of form data to send in the request body.
        :type data: dict, optional
        :param json: Dictionary of JSON data to send in the request body.
        :type json: dict, optional
        :return: A JSON response from the API if the request is successful; 
        otherwise, a dictionary with an "error" key
        containing the error message.
        :rtype: dict
        """
        try:
            response = requests.post(f"{cls.API_URL}{endpoint}", data=data, json=json)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
