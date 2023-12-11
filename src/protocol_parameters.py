import src.hashstack
import src.nostra_alpha
import src.nostra_mainnet
import src.zklend



# TODO: make this an attribute of the State class? Or get it from the name of the protocol?
def get_directory(state: src.state.State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, src.zklend.ZkLendState):
        return "zklend_data"
    if isinstance(state, src.hashstack.HashstackState):
        return "hashstack_data"
    if isinstance(state, src.nostra_alpha.NostraAlphaState) and not isinstance(state, src.nostra_mainnet.NostraMainnetState):
        return "nostra_alpha_data"
    if isinstance(state, src.nostra_mainnet.NostraMainnetState):
        return "nostra_mainnet_data"
    raise ValueError


# TODO: make this an attribute of the State class?
def get_protocol(state: src.state.State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, src.zklend.ZkLendState):
        return "zkLend"
    if isinstance(state, src.hashstack.HashstackState):
        return "Hashstack"
    if isinstance(state, src.nostra_alpha.NostraAlphaState) and not isinstance(state, src.nostra_mainnet.NostraMainnetState):
        return "Nostra Alpha"
    if isinstance(state, src.nostra_mainnet.NostraMainnetState):
        return "Nostra Mainnet"
    raise ValueError


# TODO: make this an attribute of the State class?
def get_supply_function_call_parameters(protocol: str, token: str) -> tuple[str, str]:
    if protocol == 'zkLend':
        return src.zklend.TOKEN_SETTINGS[token].protocol_token_address, 'felt_total_supply'
    if protocol in {'Nostra Alpha', 'Nostra Mainnet'}:
        return src.nostra_alpha.TOKEN_SETTINGS[token].protocol_token_address, 'totalSupply'
    raise ValueError