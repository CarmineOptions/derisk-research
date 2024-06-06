from database.crud import DBConnector
from database.models import OrderBookModel


class OrderBookProcessor:
    def __init__(self, dex, token_a, token_b):
        self.dex = dex
        self.token_a = token_a
        self.token_b = token_b

    def _set_current_price(self, order_book: OrderBookModel):
        self.current_price = order_book.asks[0][0] if order_book.asks else None

    def calculate_price_change(self):
        connector = DBConnector()
        order_book = connector.get_latest_order_book(self.dex, self.token_a, self.token_b)
        if not order_book:
            raise ValueError("No order book found for the given DEX and token pair.")
