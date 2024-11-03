"""
Module for processing order book data, allowing calculation of the quantity of a base token needed 
to impact the price by a specified ratio on various DEX platforms.
"""
from decimal import Decimal

from data_handler.db.crud import DBConnector


class OrderBookProcessor:
    """
    Processes order book data for a specified DEX and token pair, enabling calculation of the
    quantity needed to achieve a specified price change ratio.
    """

    def __init__(self, dex: str, token_a: str, token_b: str):
        """
        Initialize the order book processor.
        :param dex: The DEX name to work with.
        :param token_a: The base token address.
        :param token_b: The quote token address.
        """
        self.dex = dex
        self.token_a = token_a
        self.token_b = token_b

    def calculate_price_change(self, price_change_ratio: Decimal) -> Decimal:
        """
        Calculate quantity of `token_a` that can be bought to change the price by the given ratio.
        :param price_change_ratio: Decimal - The price change ratio.
        :return: Decimal - Quantity that can be traded without 
        moving price outside acceptable bound.
        """
        # Fetch order book
        connector = DBConnector()
        order_book = connector.get_latest_order_book(self.dex, self.token_a, self.token_b)
        if not order_book:
            raise ValueError("No order book found for the given DEX and token pair.")

        # Check current price and ratio validity
        if not (0 < price_change_ratio < 1):
            raise ValueError("Provide valid price change ratio.")
        if order_book.current_price == 0:
            raise ValueError("Current price of the pair is zero.")

        # Calculate the minimum price change
        min_price = (Decimal("1") - price_change_ratio) * order_book.current_price
        price_change = Decimal("0")
        for price, quantity in order_book.bids[::-1]:
            if price >= min_price:
                price_change += Decimal(quantity)
            elif price < min_price:
                break
        return price_change


if __name__ == "__main__":
    processor = OrderBookProcessor(
        "Starknet",
        "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    )
    uniswapv2 = processor.calculate_price_change(Decimal("0.05"))
    processor = OrderBookProcessor(
        "Ekubo",
        "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    )
    ekubo = processor.calculate_price_change(Decimal("0.05"))
    processor = OrderBookProcessor(
        "Haiko",
        "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    )
    haiko = processor.calculate_price_change(Decimal("0.05"))
