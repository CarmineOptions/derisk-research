"Test Case for SwapAmm class"

import os
import sys
from decimal import Decimal
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, patch

import pytest

# insert root directory into python module search path
sys.path.insert(1, os.getcwd())
from shared.amms import MySwapPool, Pool, SwapAmm
from shared.custom_types import TokenSettings, TokenValues


class MockPool(Pool):
    """
    Mock implementation of the Pool class for testing purposes.

    Attributes:
        base_token (TokenValues): The base token configuration
        quote_token (TokenValues): The quote token configuration
        addresses (List[str]): List of pool addresses
        id (str): Unique identifier for the pool
    """

    def __init__(
        self,
        base_token: str,
        quote_token: str,
        addresses: List[str],
        myswap_id: Optional[int] = None,
    ) -> None:
        """
        Initialize a mock pool with given token pairs and addresses.

        Args:
            base_token: Symbol of the base token
            quote_token: Symbol of the quote token
            addresses: List of contract addresses for the pool
            myswap_id: Optional MySwap pool identifier
        """
        self.base_token = TokenValues(
            TokenSettings(
                symbol=base_token,
                decimal_factor=Decimal("1000000000000000000"),
                address="0x123",
            )
        )
        self.quote_token = TokenValues(
            TokenSettings(
                symbol=quote_token, decimal_factor=Decimal("1000000"), address="0x456"
            )
        )
        self.addresses = addresses
        tokens = sorted([base_token, quote_token])
        self.id = f"{tokens[0]}/{tokens[1]}"

    async def get_balance(self) -> bool:
        """Mock implementation of balance retrieval."""
        return True

    def supply_at_price(self, initial_price: Decimal) -> Decimal:
        """
        Mock implementation of supply calculation at a given price.

        Args:
            initial_price: The price point to calculate supply for

        Returns:
            A fixed decimal value for testing
        """
        return Decimal("1000.0")


class MockMySwapPool(MySwapPool):
    """
    Mock implementation of the MySwapPool class for testing purposes.

    Attributes:
        base_token (TokenValues): The base token configuration
        quote_token (TokenValues): The quote token configuration
        addresses (List[str]): List of pool addresses
        myswap_id (int): MySwap pool identifier
        id (str): Unique identifier for the pool
    """

    def __init__(
        self, base_token: str, quote_token: str, addresses: List[str], myswap_id: int
    ) -> None:
        """
        Initialize a mock MySwap pool with given token pairs and addresses.

        Args:
            base_token: Symbol of the base token
            quote_token: Symbol of the quote token
            addresses: List of contract addresses for the pool
            myswap_id: MySwap pool identifier
        """
        self.base_token = TokenValues(
            TokenSettings(
                symbol=base_token,
                decimal_factor=Decimal("1000000000000000000"),
                address="0x123",
            )
        )
        self.quote_token = TokenValues(
            TokenSettings(
                symbol=quote_token, decimal_factor=Decimal("1000000"), address="0x456"
            )
        )
        self.addresses = addresses
        self.myswap_id = myswap_id
        tokens = sorted([base_token, quote_token])
        self.id = f"{tokens[0]}/{tokens[1]}"

    async def get_balance(self) -> bool:
        """Mock implementation of balance retrieval."""
        return True

    def supply_at_price(self, initial_price: Decimal) -> Decimal:
        """
        Mock implementation of supply calculation at a given price.

        Args:
            initial_price: The price point to calculate supply for

        Returns:
            A fixed decimal value for testing
        """
        return Decimal("1000.0")


@pytest.fixture
def mock_token_settings() -> Dict[str, TokenSettings]:
    """
    Fixture providing mock token settings for testing.

    Returns:
        Dictionary mapping token symbols to their settings
    """
    return {
        "ETH": TokenSettings(
            symbol="ETH",
            decimal_factor=Decimal("1000000000000000000"),
            address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        ),
        "USDC": TokenSettings(
            symbol="USDC",
            decimal_factor=Decimal("1000000"),
            address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        ),
        "BTC": TokenSettings(
            symbol="BTC",
            decimal_factor=Decimal("100000000"),
            address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        ),
        "DAI": TokenSettings(
            symbol="DAI",
            decimal_factor=Decimal("1000000000000000000"),
            address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        ),
    }


@pytest.fixture
def mock_pool_mapping() -> Dict[str, Dict[str, any]]:
    """
    Fixture providing mock pool mappings for testing.

    Returns:
        Dictionary mapping pool IDs to their configuration
    """
    return {
        "ETH/USDC": {
            "base_token": "ETH",
            "quote_token": "USDC",
            "addresses": [
                "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
                "0x030615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f",
            ],
            "myswap_id": 1,
        }
    }


@pytest.fixture
def swap_amm(
    mock_token_settings: Dict[str, TokenSettings],
    mock_pool_mapping: Dict[str, Dict[str, any]],
) -> SwapAmm:
    """
    Fixture providing a SwapAmm instance with mock dependencies.

    Args:
        mock_token_settings: Mock token settings
        mock_pool_mapping: Mock pool mappings

    Returns:
        Configured SwapAmm instance for testing
    """
    with patch("shared.constants.TOKEN_SETTINGS", mock_token_settings), patch(
        "shared.constants.POOL_MAPPING", mock_pool_mapping
    ), patch("shared.amms.Pool", MockPool), patch(
        "shared.amms.MySwapPool", MockMySwapPool
    ):
        return SwapAmm()


class TestSwapAmmPositive:
    """Test suite for positive test cases of the SwapAmm class."""

    def test_initialization(
        self,
        swap_amm: SwapAmm,
    ) -> None:
        """
        Test successful initialization of SwapAmm.

        Args:
            swap_amm: SwapAmm instance
            mock_pool_mapping: Mock pool configuration
        """
        assert isinstance(swap_amm.pools, Dict)
        pool = swap_amm.pools.get("ETH/USDC")
        assert isinstance(pool, MockMySwapPool)
        assert pool.myswap_id == 1

    def test_add_pool_regular(
        self, swap_amm: SwapAmm, mock_token_settings: Dict[str, TokenSettings]
    ) -> None:
        """
        Test adding a regular pool.

        Args:
            swap_amm: SwapAmm instance
            mock_token_settings: Mock token settings
        """
        with patch("shared.constants.TOKEN_SETTINGS", mock_token_settings), patch(
            "shared.amms.Pool", MockPool
        ):
            swap_amm.add_pool(
                base_token="BTC",
                quote_token="USDC",
                pool_addresses=["0xaddress1", "0xaddress2"],
                myswap_id=None,
            )
            pool = swap_amm.get_pool("BTC", "USDC")
            assert isinstance(pool, MockPool)
            assert not isinstance(pool, MockMySwapPool)
            assert pool.addresses == ["0xaddress1", "0xaddress2"]
            assert isinstance(pool.base_token, TokenValues)
            assert isinstance(pool.quote_token, TokenValues)
            assert pool.base_token.values.symbol == "BTC"
            assert pool.quote_token.values.symbol == "USDC"

    def test_add_pool_myswap(
        self, swap_amm: SwapAmm, mock_token_settings: Dict[str, TokenSettings]
    ) -> None:
        """
        Test adding a MySwap pool.

        Args:
            swap_amm: SwapAmm instance
            mock_token_settings: Mock token settings
        """
        with patch("shared.constants.TOKEN_SETTINGS", mock_token_settings), patch(
            "shared.amms.MySwapPool", MockMySwapPool
        ):
            swap_amm.add_pool(
                base_token="DAI",
                quote_token="USDC",
                pool_addresses=["0xaddress3"],
                myswap_id=2,
            )
            pool = swap_amm.get_pool("DAI", "USDC")
            assert isinstance(pool, MockMySwapPool)
            assert pool.myswap_id == 2
            assert isinstance(pool.base_token, TokenValues)
            assert isinstance(pool.quote_token, TokenValues)
            assert pool.base_token.values.symbol == "DAI"
            assert pool.quote_token.values.symbol == "USDC"

    @pytest.mark.asyncio
    async def test_get_balance(self, swap_amm: SwapAmm) -> None:
        """
        Test getting balances for all pools.

        Args:
            swap_amm: SwapAmm instance
        """
        for pool in swap_amm.pools.values():
            pool.get_balance = AsyncMock(return_value=True)

        await swap_amm.get_balance()

        for pool in swap_amm.pools.values():
            pool.get_balance.assert_called_once()

    def test_get_pool_exists(self, swap_amm: SwapAmm) -> None:
        """
        Test retrieving an existing pool.

        Args:
            swap_amm: SwapAmm instance
        """
        pool = swap_amm.get_pool("ETH", "USDC")
        assert isinstance(pool, MockMySwapPool)
        assert pool.base_token.values.symbol == "ETH"
        assert pool.quote_token.values.symbol == "USDC"

    def test_get_supply_at_price(self, swap_amm: SwapAmm) -> None:
        """
        Test calculating supply at a given price.

        Args:
            swap_amm: SwapAmm instance
        """
        supply = swap_amm.get_supply_at_price(
            collateral_token_underlying_symbol="ETH",
            collateral_token_price=1500.0,
            debt_token_underlying_symbol="USDC",
            amm="jediswap",
        )
        assert isinstance(supply, Decimal)
        assert supply == Decimal("1000.0")

    def test_token_pair_order_independence(self, swap_amm: SwapAmm) -> None:
        """
        Test that token pair ordering doesn't matter when getting a pool.

        Args:
            swap_amm: SwapAmm instance
        """
        pool1 = swap_amm.get_pool("ETH", "USDC")
        pool2 = swap_amm.get_pool("USDC", "ETH")
        assert pool1 == pool2
        assert pool1.id == pool2.id


class TestSwapAmmNegative:
    """Test suite for negative test cases of the SwapAmm class."""

    def test_get_nonexistent_pool(self, swap_amm: SwapAmm) -> None:
        """
        Test getting a pool that doesn't exist.

        Args:
            swap_amm: SwapAmm instance

        Raises:
            ValueError: When attempting to get a non-existent pool
        """
        with pytest.raises(ValueError) as exc_info:
            swap_amm.get_pool("NONEXISTENT", "TOKEN")
        assert "Trying to get pools that are not set" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_balance_failure(self, swap_amm: SwapAmm) -> None:
        """
        Test handling of balance retrieval failure.

        Args:
            swap_amm: SwapAmm instance

        Raises:
            Exception: When balance retrieval fails
        """
        error_message = "Network error"
        for pool in swap_amm.pools.values():
            pool.get_balance = AsyncMock(side_effect=Exception(error_message))

        with pytest.raises(Exception) as exc_info:
            await swap_amm.get_balance()
        assert error_message in str(exc_info.value)

    def test_get_supply_at_price_invalid_tokens(self, swap_amm: SwapAmm) -> None:
        """
        Test getting supply with invalid token pair.

        Args:
            swap_amm: SwapAmm instance

        Raises:
            ValueError: When using invalid token symbols
        """
        with pytest.raises(ValueError):
            swap_amm.get_supply_at_price(
                collateral_token_underlying_symbol="INVALID",
                collateral_token_price=100.0,
                debt_token_underlying_symbol="TOKEN",
                amm="jediswap",
            )

    def test_add_duplicate_pool(self, swap_amm, mock_token_settings):
        """Test adding a duplicate pool."""
        with patch("shared.constants.TOKEN_SETTINGS", mock_token_settings), patch(
            "shared.amms.Pool", MockPool
        ):
            # Get the initial pool
            initial_pool = swap_amm.get_pool("ETH", "USDC")
            initial_addresses = initial_pool.addresses.copy()

            # Add the same pool with different addresses
            new_addresses = ["0xnewaddress"]
            swap_amm.add_pool(
                base_token="ETH",
                quote_token="USDC",
                pool_addresses=new_addresses,
                myswap_id=None,
            )

            # Verify the pool was overwritten
            new_pool = swap_amm.get_pool("ETH", "USDC")
            assert new_pool.addresses != initial_addresses
            assert new_pool.addresses == new_addresses
            assert isinstance(new_pool, MockPool)
            assert not isinstance(new_pool, MockMySwapPool)


# Parametrized Tests
@pytest.mark.parametrize(
    "token_pair,expected_id",
    [
        (("ETH", "USDC"), "ETH/USDC"),
        (("USDC", "ETH"), "ETH/USDC"),  # Test order independence
        (("BTC", "ETH"), "BTC/ETH"),
    ],
)
def test_tokens_to_id(token_pair, expected_id, swap_amm):
    """Test token pair ID generation with different combinations."""
    base_token, quote_token = token_pair
    # Sort tokens to match the implementation's behavior
    tokens = sorted([base_token, quote_token])
    expected_id = f"{tokens[0]}/{tokens[1]}"
    assert swap_amm.tokens_to_id(base_token, quote_token) == expected_id
