""" Test Cases for MySwap"""

import asyncio
import math
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ...handlers.order_books.myswap.main import MySwapOrderBook

MAX_MYSWAP_TICK = Decimal("1774532")


@pytest.fixture
def order_book():
    """Mocks"""
    obj = MySwapOrderBook(
        base_token="0x12345", quote_token="0x67890", apply_filtering=True
    )
    obj.base_token = "0x12345"
    obj.quote_token = "0x67890"
    return obj


def test_order_book_initialization(order_book):
    """Test that the order book is initialized correctly."""
    assert order_book.base_token == "0x12345"
    assert order_book.quote_token == "0x67890"
    assert order_book.apply_filtering is True


def test_price_to_tick(order_book):
    """Test conversion of price to tick."""
    order_book._decimals_diff = Decimal(1)
    price = Decimal("1.0001")
    tick = order_book._price_to_tick(price)
    expected_tick = (
        round(
            Decimal(math.log(price / (Decimal(2**128) * order_book._decimals_diff)))
            / Decimal(math.log(Decimal("1.0001")))
        )
        + MAX_MYSWAP_TICK
    )
    assert tick == expected_tick


@patch.object(MySwapOrderBook, "_get_clean_addresses", return_value=("0x123", "0x456"))
def test_filter_pools_data(mock_get_clean_addresses, order_book):
    """Test that the pool data is correctly filtered."""
    all_pools = {
        "pools": [
            {"token0": {"address": "0x123"}, "token1": {"address": "0x456"}},
            {"token0": {"address": "0x999"}, "token1": {"address": "0x888"}},
        ]
    }
    filtered = order_book._filter_pools_data(all_pools)
    assert len(filtered) == 1
    assert filtered[0]["token0"]["address"] == "0x123"


@patch.object(
    MySwapOrderBook, "_filter_pools_data", return_value=[{"poolkey": "test_pool"}]
)
@patch.object(MySwapOrderBook, "_calculate_order_book", new_callable=AsyncMock)
def test_async_fetch_price_and_liquidity(
    mock_calculate_order_book, mock_filter_pools, order_book
):
    """Test the async fetching of price and liquidity."""
    order_book.connector = Mock()
    order_book.connector.get_pools_data = Mock(return_value={"pools": []})

    async def run_test():
        await order_book._async_fetch_price_and_liquidity()

    asyncio.run(run_test())
    mock_calculate_order_book.assert_awaited_once_with("test_pool")


@patch.object(MySwapOrderBook, "_get_clean_addresses", return_value=("0x123", "0x456"))
def test_filter_pools_data_no_match(mock_get_clean_addresses, order_book):
    """Test filtering when no pools match."""
    all_pools = {
        "pools": [
            {"token0": {"address": "0x999"}, "token1": {"address": "0x888"}},
        ]
    }
    filtered = order_book._filter_pools_data(all_pools)
    assert len(filtered) == 0


def test_price_to_tick_invalid(order_book):
    """Test invalid price leading to ValueError."""
    order_book._decimals_diff = Decimal(1)
    with pytest.raises(ValueError):
        order_book._price_to_tick(Decimal(0))


@patch.object(MySwapOrderBook, "_filter_pools_data", return_value=[])
def test_async_fetch_price_and_liquidity_no_pools(mock_filter_pools, order_book):
    """Test the async fetching when no pools are available."""
    order_book.connector = Mock()
    order_book.connector.get_pools_data = Mock(return_value={"pools": []})

    async def run_test():
        await order_book._async_fetch_price_and_liquidity()

    asyncio.run(run_test())
    mock_filter_pools.assert_called_once()
