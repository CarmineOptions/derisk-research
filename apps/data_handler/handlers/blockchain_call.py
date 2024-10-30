"""
Starknet blockchain interaction module for the data handler application.
Provides functions for making contract calls and fetching token balances and pool data
from MySwap on the Starknet network.

This module handles:
- Contract function calls
- Token balance queries
- MySwap pool data retrieval
"""

import time
import starknet_py.cairo.felt
import starknet_py.hash.selector
import starknet_py.net.client_models
import starknet_py.net.networks
from starknet_py.net.full_node_client import FullNodeClient

# Initialize StarkNet client with mainnet endpoint
NET = FullNodeClient(node_url="https://starknet-mainnet.public.blastapi.io")


async def func_call(addr: int, selector: str, calldata: list) -> list:
    """
    Make a contract call to StarkNet.

    Args:
        addr: Contract address as integer
        selector: Function name to call
        calldata: List of call parameters

    Returns:
        List of response data from the contract call

    Raises:
        Exception: Retries once after 10 seconds if first call fails
    """
    call = starknet_py.net.client_models.Call(
        to_addr=addr,
        selector=starknet_py.hash.selector.get_selector_from_name(selector),
        calldata=calldata,
    )

    try:
        res = await NET.call_contract(call)
    except:
        time.sleep(10)
        res = await NET.call_contract(call)
    return res


async def balance_of(token_addr: str, holder_addr: str) -> int:
    """
    Get token balance for a specific address.

    Args:
        token_addr: Token contract address in hex format
        holder_addr: Address to check balance for in hex format

    Returns:
        Token balance as integer
    """
    res = await func_call(int(token_addr, base=16), "balanceOf", [int(holder_addr, base=16)])
    return res[0]


async def get_myswap_pool(id: int) -> dict:
    """
    Fetch MySwap pool data by pool ID.

    Args:
        id: Pool ID to query

    Returns:
        Dictionary containing pool information:
            - token1: First token symbol
            - token2: Second token symbol
            - token1_address: First token contract address
            - token1_amount: First token amount in pool
            - token2_address: Second token contract address
            - token2_amount: Second token amount in pool
            Also includes amounts mapped to token symbols

    Note:
        Uses hardcoded MySwap contract address:
        0x67b53c94bdcd698393f0a27eba990f7ded18d3b7eb3ed0a1da48282773e1f5c8
    """
    MYSWAP_CONTRACT = 467359278613506166151492726487752216059557962335532790304583050955123345960

    res = await func_call(
        MYSWAP_CONTRACT,
        "get_pool",
        [id],
    )

    # Decode pool name (e.g., "MYSWAP ETH/USDC")
    pool_name = starknet_py.cairo.felt.decode_shortstring(res[0])
    # Extract token symbols (e.g., ["ETH", "USDC"])
    tokens = pool_name.split()[1].split("/")

    pool = {
        "token1": tokens[0],
        "token2": tokens[1],
        "token1_address": res[1],
        "token1_amount": res[2],
        "token2_address": res[4],
        "token2_amount": res[5],
        tokens[0]: res[2],
        tokens[1]: res[5],
    }

    return pool
