from starknet_py.net.gateway_client import GatewayClient
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from starknet_py.net.networks import MAINNET


NET = GatewayClient(MAINNET)


async def func_call(addr, selector, calldata):
    call = Call(
        to_addr=addr, selector=get_selector_from_name(selector), calldata=calldata
    )
    res = await NET.call_contract(call)
    return res


async def balance_of(token_addr, holder_addr):
    res = await func_call(
        int(token_addr, base=16), "balanceOf", [int(holder_addr, base=16)]
    )
    return res[0]
