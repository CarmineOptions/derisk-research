import pytest
pytest.importorskip("data_handler")
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

@pytest.mark.parametrize("collateral_price, expected_count", [
    (100, 47)
])
def test_get_collateral_token_range(collateral_price, expected_count):
    """Tests if get_collateral_token_range returns the expected number of prices."""
    result = get_collateral_token_range("0xAddress", collateral_price)
    assert len(result) == expected_count
    assert all(isinstance(price, float) for price in result)

@pytest.mark.parametrize("collateral_price, expected_count", [
    (0, 1)
])
@pytest.mark.xfail(reason="Invalid input (zero price)")
def test_get_collateral_token_range_invalid(collateral_price, expected_count):
    """Tests get_collateral_token_range with an invalid zero price input."""
    result = get_collateral_token_range("0xAddress", collateral_price)
    assert len(result) == expected_count

def test_add_leading_zeros():
    """Tests if add_leading_zeros correctly formats the hash string."""
    hash_str = "0x123456789abcdef"
    result = add_leading_zeros(hash_str)
    assert len(result) == 66
    assert result.startswith("0x")

def test_get_addresses():
    """Tests if get_addresses correctly returns the expected token addresses."""
    mock_params = {
        "token1": MockToken("0xabc", "underlying1"),
        "token2": MockToken("0xdef", "underlying2"),
    }
    result = get_addresses(mock_params, underlying_symbol="underlying1")
    assert result == ["0xabc"]

def test_get_custom_data():
    """Tests if get_custom_data correctly extracts liquidable_debt_at_interval."""
    df = pd.DataFrame({
        "liquidable_debt_at_interval": [1, 2, 3],
    })
    result = get_custom_data(df)
    assert len(result) == 3

class MockToken:
    def __init__(self, address, underlying_symbol, underlying_address=None):
        """Mock Token class to simulate token behavior."""
        self.address = address
        self.underlying_symbol = underlying_symbol
        self.underlying_address = underlying_address or address

def test_get_underlying_address():
    """Tests if get_underlying_address correctly returns the expected address."""
    token_parameters = {
        "token1": MockToken("0xabc", "TOKEN_A", "0x111"),
        "token2": MockToken("0xdef", "TOKEN_B", "0x222"),
    }
    result = get_underlying_address(token_parameters, "TOKEN_A")
    assert result == "0x111"
    result = get_underlying_address(token_parameters, "TOKEN_B")
    assert result == "0x222"
    result = get_underlying_address(token_parameters, "TOKEN_X")
    assert result == ""
    token_parameters["token3"] = MockToken("0xghi", "TOKEN_A", "0x333")
    with pytest.raises(AssertionError):
        get_underlying_address(token_parameters, "TOKEN_A")

def test_get_prices():
    """Tests if get_prices correctly fetches and processes token prices."""
    formatted_address = add_leading_zeros("0x123")
    mock_response = [{"address": formatted_address, "currentPrice": 50, "decimals": 18}]
    token_decimals = {formatted_address: 18}
    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response
        result = get_prices(token_decimals)
        assert result[formatted_address] == 50

async def test_get_symbol():
    """Tests if get_symbol correctly retrieves the symbol for a given address."""
    mock_func_call = AsyncMock(return_value=["TOKEN"])
    with patch("dashboard_app.helpers.tools.func_call", mock_func_call):
        result = await get_symbol("0x123")
        assert result == "TOKEN"

class MockState:
    class TokenParams:
        collateral = {"token1": MockToken("0xabc", "COLLATERAL", "0xabc")}
        debt = {"token2": MockToken("0xdef", "DEBT", "0xdef")}
    token_parameters = TokenParams()

    def compute_liquidable_debt_at_price(self, *args, **kwargs):
        return 10

class MockSwapAmm:
    def get_supply_at_price(self, *args, **kwargs):
        return 5

def test_get_main_chart_data():
    """Tests if get_main_chart_data correctly generates a DataFrame with required columns."""
    state = MockState()
    prices = {"0xabc": 100, "0xdef": 50}
    swap_amms = MockSwapAmm()
    result = get_main_chart_data(state, prices, swap_amms, "COLLATERAL", "DEBT")
    assert isinstance(result, pd.DataFrame)
    assert "collateral_token_price" in result.columns
