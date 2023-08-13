import starknet_py.net.gateway_client
import starknet_py.hash.selector
import starknet_py.net.client_models
import starknet_py.net.networks


NET = starknet_py.net.gateway_client.GatewayClient(starknet_py.net.networks.MAINNET)


async def func_call(addr, selector, calldata):
    call = starknet_py.net.client_models.Call(
        to_addr=addr, selector=starknet_py.hash.selector.get_selector_from_name(selector), calldata=calldata
    )
    res = await NET.call_contract(call)
    return res


async def balance_of(token_addr, holder_addr):
    res = await func_call(
        int(token_addr, base=16), "balanceOf", [int(holder_addr, base=16)]
    )
    return res[0]
