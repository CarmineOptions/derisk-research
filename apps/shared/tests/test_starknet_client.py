import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from starknet_py.net.networks import Network

from shared.starknet_client import StarknetClient

TEST_NODE_URL = "https://test.starknet.io"
TEST_CONTRACT_ADDRESS = 123456
TEST_ACCOUNT_ADDRESS = 789012
TEST_POOL_ADDRESS = 345678

class TestStarknetClient:
    """Test cases for StarknetClient class"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment with mocked Network"""
        self.network_patcher = patch('shared.starknet_client.Network')
        self.mock_network_class = self.network_patcher.start()
        self.mock_network = Mock()
        self.mock_network.call_contract = AsyncMock()
        self.mock_network_class.return_value = self.mock_network
        yield
        self.network_patcher.stop()

    def test_initialization(self):
        """Test client initialization"""
        # Test default URL
        StarknetClient()
        self.mock_network_class.assert_called_with("https://starknet-mainnet.public.blastapi.io")
        
        # Test custom URL
        self.mock_network_class.reset_mock()
        StarknetClient(TEST_NODE_URL)
        self.mock_network_class.assert_called_with(TEST_NODE_URL)

    @pytest.mark.asyncio
    async def test_func_call(self):
        """Test function call with success and retry"""
        client = StarknetClient()
        self.mock_network.call_contract.return_value = [100]

        result = await client.func_call(
            TEST_CONTRACT_ADDRESS,
            "test_function",
            [1, 2, 3]
        )

        expected_call = Call(
            to_addr=TEST_CONTRACT_ADDRESS,
            selector=get_selector_from_name("test_function"),
            calldata=[1, 2, 3]
        )
        self.mock_network.call_contract.assert_called_with(expected_call)
        assert result == [100]

    @pytest.mark.asyncio
    async def test_func_call_retry(self):
        """Test function call retry mechanism"""
        client = StarknetClient()
        self.mock_network.call_contract.side_effect = [
            Exception("Network error"),
            [100]
        ]

        result = await client.func_call(
            TEST_CONTRACT_ADDRESS,
            "test_function",
            [1, 2, 3],
            retries=1
        )

        assert self.mock_network.call_contract.call_count == 2
        assert result == [100]

    @pytest.mark.asyncio
    async def test_balance_of(self):
        """Test balance_of method"""
        client = StarknetClient()
        self.mock_network.call_contract.return_value = [1000]

        balance = await client.balance_of(TEST_CONTRACT_ADDRESS, TEST_ACCOUNT_ADDRESS)

        assert balance == Decimal('1000')
        assert self.mock_network.call_contract.call_count == 1

    @pytest.mark.asyncio
    async def test_balance_of_empty_result(self):
        """Test balance_of with empty result"""
        client = StarknetClient()
        self.mock_network.call_contract.return_value = []

        balance = await client.balance_of(TEST_CONTRACT_ADDRESS, TEST_ACCOUNT_ADDRESS)
        assert balance == Decimal('0')

    @pytest.mark.asyncio
    async def test_get_myswap_pool_with_addresses(self):
        """Test get_myswap_pool with provided token addresses"""
        client = StarknetClient()
        self.mock_network.call_contract.return_value = [100, 200]
        
        pool_info = await client.get_myswap_pool(
            TEST_POOL_ADDRESS,
            token_a_address=111,
            token_b_address=222
        )

        assert pool_info == {
            "address": TEST_POOL_ADDRESS,
            "token_a": 111,
            "token_b": 222,
            "reserve_a": 100,
            "reserve_b": 200
        }

    @pytest.mark.asyncio
    async def test_get_myswap_pool_without_addresses(self):
        """Test get_myswap_pool without token addresses"""
        client = StarknetClient()
        self.mock_network.call_contract.side_effect = [
            [100, 200],  # get_reserves
            [333],       # token0
            [444]        # token1
        ]

        pool_info = await client.get_myswap_pool(TEST_POOL_ADDRESS)

        assert self.mock_network.call_contract.call_count == 3
        assert pool_info == {
            "address": TEST_POOL_ADDRESS,
            "token_a": 333,
            "token_b": 444,
            "reserve_a": 100,
            "reserve_b": 200
        }

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test exception when max retries are exceeded"""
        client = StarknetClient()
        self.mock_network.call_contract.side_effect = Exception("Network error")

        with pytest.raises(Exception) as exc_info:
            await client.func_call(
                TEST_CONTRACT_ADDRESS,
                "test_function",
                [1, 2, 3],
                retries=2
            )

        assert str(exc_info.value) == "Network error"
        assert self.mock_network.call_contract.call_count == 3