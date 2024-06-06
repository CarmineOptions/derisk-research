from decimal import Decimal

from db.crud import DBConnector


class OrderBookProcessor:
    def __init__(self, dex, token_a, token_b):
        self.dex = dex
        self.token_a = token_a
        self.token_b = token_b

    def calculate_price_change(self, price_change_ratio: Decimal) -> Decimal:
        """Calculate quantity of `token_a` that can be bought to change the price by the given ratio."""
        connector = DBConnector()
        order_book = connector.get_latest_order_book(self.dex, self.token_a, self.token_b)
        if not order_book:
            raise ValueError("No order book found for the given DEX and token pair.")
        current_price = order_book.current_price
        if price_change_ratio > 1 or price_change_ratio < 0:
            raise ValueError("Provide valid price change ratio.")
        if current_price == 0:
            raise ValueError("Current price of the pair is zero.")
        min_price = (Decimal("1") - price_change_ratio) * current_price
        lower_quantity = Decimal("0")
        for price, quantity in order_book.bids[::-1]:
            if price >= min_price:
                lower_quantity += Decimal(quantity)
            elif price > current_price:
                break
        return lower_quantity


if __name__ == '__main__':
    processor = OrderBookProcessor("Starknet", "ETH", "USDC")
    uniswapv2 = processor.calculate_price_change(Decimal("0.05"))
    processor = OrderBookProcessor(
        "Ekubo",
        "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
    )
    ekubo = processor.calculate_price_change(Decimal("0.05"))
