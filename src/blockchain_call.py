from starknet_py.net.gateway_client import GatewayClient
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from starknet_py.net.networks import MAINNET
from starknet_py.cairo.felt import decode_shortstring


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


async def get_myswap_pool(id):
    res = await func_call(
        467359278613506166151492726487752216059557962335532790304583050955123345960, "get_pool", [
            id]
    )

    pool_name = decode_shortstring(res[0])  # MYSWAP ETH/USDC
    tokens = pool_name.split()[1].split("/")  # ["ETH", "USDC"]
    pool = {
        "token1": tokens[0],
        "token2": tokens[1],
        "token1_address": res[1],
        "token1_amount": res[2],
        "token2_address": res[4],
        "token2_amount": res[5],
        tokens[0]: res[2],
        tokens[1]: res[5]
    }

    return pool
