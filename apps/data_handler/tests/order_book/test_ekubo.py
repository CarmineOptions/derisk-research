"""Tests for the EkuboOrderBook class."""
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest
from data_handler.handlers.order_books.ekubo.main import EkuboOrderBook

@pytest.fixture
def mock_connector():
    """Create a mock EkuboAPIConnector."""
    with patch('data_handler.handlers.order_books.ekubo.main.EkuboAPIConnector') as mock:
        connector = mock.return_value
        connector.get_pair_price.return_value = {"price": "1.5"}
        connector.get_pools.return_value = [{
            "token0": "0x1",
            "token1": "0x2",
            "key_hash": "0xabc",
            "liquidity": "1000000",
            "lastUpdate": {"event_id": "123"},
            "tick": 100,
            "tick_spacing": 10
        }]
        connector.get_pool_liquidity.return_value = {
            "data": [
                {"tick": 90, "net_liquidity_delta_diff": "100"},
                {"tick": 100, "net_liquidity_delta_diff": "200"},
                {"tick": 110, "net_liquidity_delta_diff": "300"}
            ]
        }
        yield connector

@pytest.fixture
def order_book(mock_connector):
    """Create an EkuboOrderBook instance with mocked connector."""
    book = EkuboOrderBook("0x1", "0x2")
    # Set decimals for token precision
    book.token_a_decimal = 18
    book.token_b_decimal = 18
    return book

def test_initialization(order_book):
    """Test EkuboOrderBook initialization."""
    assert order_book.DEX == "Ekubo"
    assert order_book.token_a == "0x1"
    assert order_book.token_b == "0x2"
    assert order_book.asks == []
    assert order_book.bids == []

def test_set_current_price(order_book):
    """Test setting current price."""
    order_book.set_current_price()
    assert order_book.current_price == Decimal("1.5")

def test_fetch_price_and_liquidity(order_book):
    """Test fetching price and liquidity data."""
    order_book.fetch_price_and_liquidity()
    assert order_book.block == "123"
    assert len(order_book.asks) > 0
    assert len(order_book.bids) > 0

def test_calculate_order_book(order_book):
    """Test order book calculation."""
    # Create test data with ticks both above and below the current tick (100)
    liquidity_data = [
        {"tick": 90, "net_liquidity_delta_diff": "100"},
        {"tick": 95, "net_liquidity_delta_diff": "150"},
        {"tick": 100, "net_liquidity_delta_diff": "200"},
        {"tick": 105, "net_liquidity_delta_diff": "250"},
        {"tick": 110, "net_liquidity_delta_diff": "300"}
    ]
    
    # Create a pandas Series for the row
    row_data = {
        "tick": 100,
        "tick_spacing": 5,
        "liquidity": "1000000"
    }
    row = pd.Series(row_data)
    
    # Set current price for price range calculation
    order_book.current_price = Decimal("1.5")
    
    # Calculate order book
    order_book._calculate_order_book(liquidity_data, 1000000, row)
    
    # Verify that both asks and bids are populated
    assert len(order_book.asks) > 0, "Asks should not be empty"
    assert len(order_book.bids) > 0, "Bids should not be empty"
    
    # Verify the structure of asks and bids
    for price, supply in order_book.asks:
        assert isinstance(price, Decimal), "Price should be Decimal"
        assert isinstance(supply, Decimal), "Supply should be Decimal"
        assert price > 0, "Price should be positive"
        assert supply > 0, "Supply should be positive"
    
    for price, supply in order_book.bids:
        assert isinstance(price, Decimal), "Price should be Decimal"
        assert isinstance(supply, Decimal), "Supply should be Decimal"
        assert price > 0, "Price should be positive"
        assert supply > 0, "Supply should be positive"

def test_get_pure_sqrt_ratio(order_book):
    """Test square root ratio calculation."""
    result = order_book._get_pure_sqrt_ratio(Decimal("1"))
    assert isinstance(result, Decimal)
    assert result > 0

def test_sort_ticks_by_asks_and_bids():
    """Test sorting ticks into asks and bids."""
    liquidity_data = [
        {"tick": 90},
        {"tick": 100},
        {"tick": 110}
    ]
    current_tick = 100
    asks, bids = EkuboOrderBook.sort_ticks_by_asks_and_bids(liquidity_data, current_tick)
    assert len(asks) == 1
    assert len(bids) == 2
    assert all(tick["tick"] > current_tick for tick in asks)
    assert all(tick["tick"] <= current_tick for tick in bids)

def test_calculate_liquidity_amount(order_book):
    """Test liquidity amount calculation."""
    # Set token decimals for proper calculation
    order_book.token_a_decimal = 18
    order_book.token_b_decimal = 18
    
    tick = Decimal("100")
    liquidity_total = Decimal("1000000")
    result = order_book.calculate_liquidity_amount(tick, liquidity_total)
    assert isinstance(result, Decimal)
    assert result > 0

@pytest.mark.parametrize("tick,expected_sign", [
    (1000, 1),  # positive tick
    (-1000, -1),  # negative tick
    (0, 0)  # zero tick
])
def test_tick_edge_cases(order_book, tick, expected_sign):
    """Test tick calculations with edge cases."""
    result = order_book._get_pure_sqrt_ratio(Decimal(tick))
    assert isinstance(result, Decimal)
    assert result > 0  # sqrt ratio should always be positive
    if expected_sign > 0:
        assert result > 1
    elif expected_sign < 0:
        assert result < 1

def test_empty_liquidity_data(order_book):
    """Test behavior with empty liquidity data."""
    row_data = {
        "tick": 100,
        "tick_spacing": 5,
        "liquidity": "1000000"
    }
    row = pd.Series(row_data)
    
    order_book._calculate_order_book([], 1000000, row)
    assert len(order_book.asks) == 0
    assert len(order_book.bids) == 0