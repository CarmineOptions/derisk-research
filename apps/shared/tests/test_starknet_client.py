import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from starknet_py.net.networks import Network

from shared.starknet_client import StarknetClient

# Test constants
TEST_NODE_URL = "https://test.starknet.io"
TEST_CONTRACT_ADDRESS = 123456
TEST_ACCOUNT_ADDRESS = 789012
TEST_POOL_ADDRESS = 345678

@pytest.fixture
def mock_network():
    """Fixture for mocked Network instance"""
    with patch('shared.starknet_client.Network') as mock_network:
        network_instance = Mock()
        network_instance.call_contract = AsyncMock()
        mock_network.return_value = network_instance
        yield network_instance

@pytest.fixture
def client(mock_network):
    """Fixture for StarknetClient instance with mocked network"""
    return StarknetClient(TEST_NODE_URL)

class TestStarknetClientPositive:
    """Positive test cases for StarknetClient"""

    def test_initialization(self, mock_network):
        """Test client initialization with default and custom URLs"""
        # Test default URL
        client = StarknetClient()
        mock_network.assert_called_with("https://starknet-mainnet.public.blastapi.io")

        # Test custom URL
        client = StarknetClient(TEST_NODE_URL)
        mock_network.assert_called_with(TEST_NODE_URL)

    @pytest.mark.asyncio
    async def test_func_call_success(self, client, mock_network):
        """Test successful contract function call"""
        mock_network.call_contract.return_value = [100]
        
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
        mock_network.call_contract.assert_called_once_with(expected_call)
        assert result == [100]

    @pytest.mark.asyncio
    async def test_balance_of(self, client, mock_network):
        """Test balance_of method"""
        mock_network.call_contract.return_value = [1000]
        
        balance = await client.balance_of(TEST_CONTRACT_ADDRESS, TEST_ACCOUNT_ADDRESS)
        
        expected_call = Call(
            to_addr=TEST_CONTRACT_ADDRESS,
            selector=get_selector_from_name("balanceOf"),
            calldata=[TEST_ACCOUNT_ADDRESS]
        )
        mock_network.call_contract.assert_called_once_with(expected_call)
        assert balance == Decimal('1000')

    @pytest.mark.asyncio
    async def test_get_myswap_pool_with_token_addresses(self, client, mock_network):
        """Test get_myswap_pool with provided token addresses"""
        mock_network.call_contract.return_value = [100, 200]
        token_a_addr = 111
        token_b_addr = 222
        
        pool_info = await client.get_myswap_pool(
            TEST_POOL_ADDRESS,
            token_a_addr,
            token_b_addr
        )
        
        expected_call = Call(
            to_addr=TEST_POOL_ADDRESS,
            selector=get_selector_from_name("get_reserves"),
            calldata=[]
        )
        mock_network.call_contract.assert_called_once_with(expected_call)
        
        assert pool_info == {
            "address": TEST_POOL_ADDRESS,
            "token_a": token_a_addr,
            "token_b": token_b_addr,
            "reserve_a": 100,
            "reserve_b": 200
        }

    @pytest.mark.asyncio
    async def test_get_myswap_pool_without_token_addresses(self, client, mock_network):
        """Test get_myswap_pool without token addresses"""
        # Mock sequential calls for reserves, token0, and token1
        mock_network.call_contract.side_effect = [
            [100, 200],  # get_reserves
            [333],       # token0
            [444]        # token1
        ]
        
        pool_info = await client.get_myswap_pool(TEST_POOL_ADDRESS)
        
        assert len(mock_network.call_contract.call_args_list) == 3
        assert pool_info == {
            "address": TEST_POOL_ADDRESS,
            "token_a": 333,
            "token_b": 444,
            "reserve_a": 100,
            "reserve_b": 200
        }

class TestStarknetClientNegative:
    """Negative test cases for StarknetClient"""

    @pytest.mark.asyncio
    async def test_func_call_retry_success(self, client, mock_network):
        """Test successful retry after initial failure"""
        mock_network.call_contract.side_effect = [
            Exception("Network error"),
            [100]
        ]
        
        result = await client.func_call(
            TEST_CONTRACT_ADDRESS,
            "test_function",
            [1, 2, 3],
            retries=1
        )
        
        assert mock_network.call_contract.call_count == 2
        assert result == [100]

    @pytest.mark.asyncio
    async def test_func_call_max_retries_exceeded(self, client, mock_network):
        """Test exception when max retries are exceeded"""
        error = Exception("Network error")
        mock_network.call_contract.side_effect = error
        
        with pytest.raises(Exception) as exc_info:
            await client.func_call(
                TEST_CONTRACT_ADDRESS,
                "test_function",
                [1, 2, 3],
                retries=2
            )
        
        assert mock_network.call_contract.call_count == 3
        assert exc_info.value == error

    @pytest.mark.asyncio
    async def test_balance_of_empty_result(self, client, mock_network):
        """Test balance_of with empty result"""
        mock_network.call_contract.return_value = []
        
        balance = await client.balance_of(TEST_CONTRACT_ADDRESS, TEST_ACCOUNT_ADDRESS)
        assert balance == Decimal('0')

    @pytest.mark.asyncio
    async def test_get_myswap_pool_network_error(self, client, mock_network):
        """Test get_myswap_pool with network error"""
        mock_network.call_contract.side_effect = Exception("Network error")
        
        with pytest.raises(Exception) as exc_info:
            await client.get_myswap_pool(TEST_POOL_ADDRESS)
        
        assert str(exc_info.value) == "Network error"