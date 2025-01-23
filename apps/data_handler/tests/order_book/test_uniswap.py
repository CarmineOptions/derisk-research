from collections.abc import Iterable
from decimal import Decimal

import pytest
from data_handler.handlers.order_books.processing import OrderBookProcessor
from data_handler.handlers.order_books.uniswap_v2 import main


@pytest.fixture
def order_book():
    """
    Fixture for the order book setup.
    token_a and token_b gotten from constants (data_handlers.handlers.order_books.constants)
    """
    token_a = "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7"
    token_b = "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8"
    order_book = main.UniswapV2OrderBook(token_a, token_b)
    return order_book


class TestUniswapV2OrderBook:
    def test_set_token_name(self, order_book: main.UniswapV2OrderBook):
        """
        Unit Test for UniswapV2OrderBook._set_token_names.
        """
        # check that token_names has not been set
        assert not getattr(order_book, "token_a_name"), "Token_a_name should be None"
        assert not getattr(order_book, "token_b_name"), "Token_b_name should be None"

        # set token name
        order_book._set_token_names()

        # check that token_names has been set
        assert order_book.token_a_name, "token_a_name should be set"
        assert order_book.token_b_name, "token_b_name should be set"

        # check that token_names match their mappings
        assert order_book.token_a_name == "ETH", "token_a_name should be ETH"
        assert order_book.token_b_name == "USDC", "token_b_name should be USDC"

    def test_tick_to_price(self, order_book: main.UniswapV2OrderBook):
        """
        Unit test for UniswapV2OrderBook.tick_to_price
        Note: calculation is based on the ETH/USDC pair
        """
        tick_value = 1000
        price_value = 1.10517
        uniswap_price_value = order_book.tick_to_price(tick_value)
        assert price_value == uniswap_price_value, "Invalid tick to price conversion"

    def test_add_quantities_data(self, order_book: main.UniswapV2OrderBook):
        pass

    def test_calculate_liquidity_amount(self):
        pass

    def test_get_prices_ranges(self, order_book: main.UniswapV2OrderBook):
        """
        Unit test for UniswapV2OrderBook.get_price_ranges
        """
        price_ranges = order_book.get_prices_range(Decimal("3012.92"))
        assert isinstance(price_ranges, Iterable), "Price ranges should be a iterable"
        assert (
            len(price_ranges) > 1
        ), "Price ranges list length should be greater than 1"

    def test_fetch_price_and_liquidity(self):
        pass


class TestUniswapV2OrderBookProcessor:
    def test_calculate_price_change_successful(self):
        """
        Check whether calculate_price_change method call is successful
        """
        processor = OrderBookProcessor(
            "Starknet",
            "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
            "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        )
        price = processor.calculate_price_change(Decimal("0.05"))
        assert isinstance(price, Decimal)  # :)

    def test_calculate_price_change_fail_with_invalid_args(self):
        """
        Check that ValueError is raised when price_change_ratio argument is
        greater than 1 or less than 0 or equal to zero
        """
        processor = OrderBookProcessor(
            "Starknet",
            "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
            "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        )
        with pytest.raises(ValueError, match="Provide valid price change ratio."):
            # check whether it is greater than
            price = processor.calculate_price_change(Decimal("5"))

        with pytest.raises(ValueError, match="Provide valid price change ratio."):
            # fails when it is less than
            price = processor.calculate_price_change(Decimal("-1"))

        with pytest.raises(ValueError, match="Current price of the pair is zero."):
            # check whether it is greater than
            price = processor.calculate_price_change(Decimal("0"))
