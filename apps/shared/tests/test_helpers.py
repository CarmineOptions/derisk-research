from ..helpers import add_leading_zeros, get_addresses, get_symbol
from ..custom_types.base import TokenParameters
from unittest.mock import AsyncMock, patch


def test_add_leading_zeros():
    """Tests if add_leading_zeros correctly formats the hash string."""
    hash_str = "0x123456789abcdef"
    result = add_leading_zeros(hash_str)
    assert len(result) == 66
    assert result.startswith("0x")


def test_get_addresses():
    """Tests if get_addresses correctly returns the expected token addresses."""
    # mock_params = {
    #     "token1": BaseTokenParameters(address="0xabc", underlying_symbol="underlying1"),
    #     "token2": BaseTokenParameters(address="0xdef", underlying_symbol="underlying2"),
    # }
    token_params = TokenParameters()
    token_params["token1"].address = "0xabc"
    token_params["token1"].underlying_symbol = "underlying1"
    token_params["token2"].address = "0xdef"
    token_params["token2"].underlying_symbol = "underlying2"
    result = get_addresses(token_params, underlying_symbol="underlying1")
    assert result == ["0xabc"]


async def test_get_symbol():
    """Tests if get_symbol correctly retrieves the symbol for a given address."""
    mock_func_call = AsyncMock(return_value=[int.from_bytes("TOKEN".encode())])
    with patch("shared.blockchain_call.func_call", mock_func_call):
        result = await get_symbol("0x123")
        assert result == "TOKEN"
