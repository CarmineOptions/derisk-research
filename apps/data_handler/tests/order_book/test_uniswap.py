import asyncio
from collections.abc import Iterable
from decimal import Decimal, ROUND_FLOOR
from unittest.mock import patch

import pytest
from data_handler.db.crud import DBConnector
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

@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture for the event loop.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


class TestUniswapV2OrderBook:
    def test_set_token_name(self, order_book: main.UniswapV2OrderBook):
        """
        Unit Test for UniswapV2OrderBook._set_token_names.
        """
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
        tick_value = Decimal("500")
        uniswap_price_value = order_book.tick_to_price(tick_value)
        assert isinstance(uniswap_price_value, Decimal), "price should be a decimal"

    def test_calculate_liquidity_amount(self, order_book: main.UniswapV2OrderBook):
        """ "
        Unit test for UniswapV2OrderBook.calculate_liquidity_amount
        """
        tick = Decimal("500")
        final_value = Decimal("9.997500313723646666869072034E-15")
        rounded_final_value = final_value.quantize(Decimal("1e-18"), rounding=ROUND_FLOOR)
        liquidity_amount = order_book.calculate_liquidity_amount(tick, Decimal("10000"))
        rounded_liquidity_value = liquidity_amount.quantize(Decimal("1e-18"), rounding=ROUND_FLOOR)
        assert rounded_final_value == rounded_liquidity_value, "liquidity amount does not match"

    def test_get_prices_ranges(self, order_book: main.UniswapV2OrderBook):
        """
        Unit test for UniswapV2OrderBook.get_price_ranges
        """
        price_ranges = order_book.get_prices_range(Decimal("3012.92"))
        assert isinstance(price_ranges, Iterable), "Price ranges should be a iterable"
        assert (
            len(price_ranges) > 1
        ), "Price ranges list length should be greater than 1"

    def test_fetch_price_and_liquidity(self, order_book: main.UniswapV2OrderBook, event_loop):
        """
        Unit test for UniswapV2OrderBook.fetch_price_and_liquidity
        """
        with patch(
            "data_handler.handlers.order_books.uniswap_v2.main.UniswapV2OrderBook._async_fetch_price_and_liquidity",
        ) as mock_fetch_price_and_liquidity:
            asyncio.set_event_loop(event_loop)
            order_book.fetch_price_and_liquidity()
            mock_fetch_price_and_liquidity.assert_called()


class TestUniswapV2OrderBookProcessor:
    def test_calculate_price_change_successful(self, mock_db_connector, monkeypatch):
        """
        Check whether calculate_price_change method call is successful
        """
        monkeypatch.setattr(DBConnector, "__new__", mock_db_connector)
        processor = OrderBookProcessor(
            "Starknet",
            "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
            "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        )
        price = processor.calculate_price_change(Decimal("0.05"))
        assert isinstance(price, Decimal)  # :)

    def test_calculate_price_change_fail_with_invalid_args(
        self, mock_db_connector, monkeypatch
    ):
        """
        Check that ValueError is raised when price_change_ratio argument is
        greater than 1 or less than 0 or equal to zero
        """
        monkeypatch.setattr(DBConnector, "__new__", mock_db_connector)
        processor = OrderBookProcessor(
            "Starknet",
            "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
            "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        )
        with pytest.raises(ValueError):
            # check whether it is greater than
            price = processor.calculate_price_change(Decimal("5"))

        with pytest.raises(ValueError):
            # fails when it is less than
            price = processor.calculate_price_change(Decimal("-1"))

        with pytest.raises(ValueError):
            # check whether it is greater than
            price = processor.calculate_price_change(Decimal("0"))
