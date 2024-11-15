import starknet_py

from .blockchain_call import func_call
from .state import State
from shared.protocol_states.zklend import ZkLendState

def add_leading_zeros(hash: str) -> str:
    """
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    """
    return "0x" + hash[2:].zfill(64)


async def get_symbol(token_address: str) -> str:
    # DAI V2's symbol is `DAI` but we don't want to mix it with DAI = DAI V1.
    if (
        token_address
        == "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad"
    ):
        return "DAI V2"
    symbol = await func_call(
        addr=token_address,
        selector="symbol",
        calldata=[],
    )
    # For some Nostra Mainnet tokens, a list of length 3 is returned.
    if len(symbol) > 1:
        return starknet_py.cairo.felt.decode_shortstring(symbol[1])
    return starknet_py.cairo.felt.decode_shortstring(symbol[0])


def get_protocol(state: State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, ZkLendState):
        return "zkLend"

    # We'll add it later

    # if isinstance(state, src.hashstack_v0.HashstackV0State):
    #     return "Hashstack V0"
    # if isinstance(state, src.hashstack_v1.HashstackV1State):
    #     return "Hashstack V1"
    # if isinstance(state, src.nostra_alpha.NostraAlphaState) and not isinstance(
    #     state, src.nostra_mainnet.NostraMainnetState
    # ):
    #     return "Nostra Alpha"
    # if isinstance(state, src.nostra_mainnet.NostraMainnetState):
    #     return "Nostra Mainnet"
    raise ValueError


def get_directory(state: State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, ZkLendState):
        return "zklend_data"

    # We'll add it later

    # if isinstance(state, src.hashstack_v0.HashstackV0State):
    #     return "hashstack_v0_data"
    # if isinstance(state, src.hashstack_v1.HashstackV1State):
    #     return "hashstack_v1_data"
    # if isinstance(state, src.nostra_alpha.NostraAlphaState) and not isinstance(
    #     state, src.nostra_mainnet.NostraMainnetState
    # ):
    #     return "nostra_alpha_data"
    # if isinstance(state, src.nostra_mainnet.NostraMainnetState):
    #     return "nostra_mainnet_data"
    raise ValueError
