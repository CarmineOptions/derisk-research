import asyncio
import time
from decimal import Decimal
from typing import Any, List, Optional, Union

from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from starknet_py.net.full_node_client import FullNodeClient


class StarknetClient:
    """
    A client class for interacting with the Starknet blockchain.
    Provides methods for making contract calls and fetching specific contract data.
    """

    def __init__(self, node_url: str = "https://starknet-mainnet.public.blastapi.io"):
        """
        Initialize StarknetClient with network URL.

        Args:
            node_url (str): The URL of the Starknet network to connect to
        """
        self.node_url = node_url
        self.client = FullNodeClient(node_url=self.node_url)

    async def func_call(
        self, addr: int, selector: str, calldata: List[int], retries: int = 1
    ) -> List[int]:
        """
        Make a call to a Starknet contract.

        Args:
            addr (int): Contract address
            selector (str): Function name to call
            calldata (List[int]): List of call arguments
            retries (int, optional): Number of retry attempts. Defaults to 1.

        Returns:
            List[int]: Contract call result
        """
        call = Call(
            to_addr=addr,
            selector=get_selector_from_name(selector),
            calldata=calldata,
        )

        for attempt in range(retries + 1):
            try:
                response = await self.client.call_contract(call, block_hash="latest")
                if hasattr(response, "result"):
                    return response.result
                elif isinstance(response, list):
                    return response
                else:
                    raise ValueError(f"Unexpected response type: {type(response)}")
            except Exception as e:
                if attempt == retries:
                    raise e
                await asyncio.sleep(10)

    async def balance_of(self, token_address: int, account_address: int) -> Decimal:
        """
        Get token balance for an account.

        Args:
            token_address (int): Address of the token contract
            account_address (int): Address of the account to check

        Returns:
            Decimal: Token balance
        """
        result = await self.func_call(token_address, "balanceOf", [account_address])
        return Decimal(result[0]) if result else Decimal(0)

    async def get_myswap_pool(
        self,
        pool_address: int,
        token_a_address: Optional[int] = None,
        token_b_address: Optional[int] = None,
    ) -> dict:
        """
        Get MySwap pool information.

        Args:
            pool_address (int): Address of the pool contract
            token_a_address (Optional[int]): Address of token A
            token_b_address (Optional[int]): Address of token B
        """
        reserves = await self.func_call(pool_address, "get_reserves", [])

        if not (token_a_address and token_b_address):
            token_a = await self.func_call(pool_address, "token0", [])
            token_b = await self.func_call(pool_address, "token1", [])
            token_a_address = token_a[0]
            token_b_address = token_b[0]

        return {
            "address": pool_address,
            "token_a": token_a_address,
            "token_b": token_b_address,
            "reserve_a": reserves[0],
            "reserve_b": reserves[1],
        }
