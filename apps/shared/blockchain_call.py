import asyncio
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from .constants import POOL_MAPPING, NET

MYSWAP_FACTORY_ADDRESS = "0x1234567890abcdef1234567890abcdef12345678"

async def func_call(call):
    res = await NET.call_contract(call)
    return res

async def get_myswap_pool(pool_id: int):
    # Avoid invalid message selector by resolving pool address from mapping
    # The MySwap factory does not expose get_pool(pool_id) with the selector used before.
    # Pool addresses are now static in POOL_MAPPING, so we return the address directly.
    for info in POOL_MAPPING.values():
        if info.get("myswap_id") == pool_id:
            return info.get("address")
    raise ValueError(f"MySwap pool id {pool_id} not found in POOL_MAPPING")

# Legacy call kept for reference - selector was incorrect
# async def get_myswap_pool_legacy(pool_id: int):
#     selector = get_selector_from_name("get_pool_by_id")
#     call = Call(to_addr=MYSWAP_FACTORY_ADDRESS, selector=selector, calldata=[int(pool_id)])
#     res = await func_call(call)
#     return res[0]
