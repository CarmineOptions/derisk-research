import pytest
import pandas as pd
from helpers.tools import (
    get_collateral_token_range,
    get_symbol,
    get_prices,
    add_leading_zeros,
    get_addresses,
    get_underlying_address,
    get_custom_data,
    get_main_chart_data
)
from unittest.mock import AsyncMock, patch

@pytest.mark.parametrize("collateral_price, expected_length", [(100, 50), (200, 50), (0, 1)])
def test_get_collateral_token_range(collateral_price, expected_length):
    result = get_collateral_token_range("0x12345", collateral_price)
    assert len(result) == expected_length
    assert all(isinstance(price, float) for price in result)

def test_add_leading_zeros():
    hash_str = "0x123456789abcdef"
    result = add_leading_zeros(hash_str)
    assert len(result) == 66  
    assert result.startswith("0x")

def test_get_addresses():
    mock_params = {
        "token1": MockToken("0xabc", "underlying1"),
        "token2": MockToken("0xdef", "underlying2"),
    }
    result = get_addresses(mock_params, underlying_symbol="underlying1")
    assert result == ["0xabc"]

def test_get_underlying_address():
    mock_params = {
        "token1": MockToken("0xabc", "underlying1"),
        "token2": MockToken("0xdef", "underlying2"),
    }
    result = get_underlying_address(mock_params, "underlying1")
    assert result == "0xabc"

def test_get_custom_data():
    df = pd.DataFrame({
        "liquidable_debt_at_interval": [1, 2, 3],
    })
    result = get_custom_data(df)
    assert len(result) == 3

def test_get_prices():
    mock_response = [{"address": "0x123", "currentPrice": 50, "decimals": 18}]
    token_decimals = {"0x123": 18}
    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response
        result = get_prices(token_decimals)
        assert result["0x123"] == 50

def test_get_symbol():
    mock_func_call = AsyncMock(return_value=["TOKEN"])
    with patch("module_name.func_call", mock_func_call):
        result = pytest.run(get_symbol("0x123"))
        assert result == "TOKEN"

def test_get_main_chart_data():
    state = MockState()
    prices = {"0xabc": 100}
    swap_amms = MockSwapAmm()
    result = get_main_chart_data(state, prices, swap_amms, "COLLATERAL", "DEBT")
    assert isinstance(result, pd.DataFrame)
    assert "collateral_token_price" in result.columns

class MockToken:
    def __init__(self, address, underlying_symbol):
        self.address = address
        self.underlying_symbol = underlying_symbol

class MockState:
    class TokenParams:
        collateral = {"token1": MockToken("0xabc", "COLLATERAL")}
        debt = {"token2": MockToken("0xdef", "DEBT")}
    token_parameters = TokenParams()
    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        return 10

class MockSwapAmm:
    def get_supply_at_price(self, *args, **kwargs):
        return 5