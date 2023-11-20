import src.hashstack
import src.nostra
import src.nostra_uncapped
import src.zklend



# TODO: make this an attribute of the State class? Or get it from the name of the protocol?
def get_directory(state: src.state.State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, src.zklend.ZkLendState):
        return "zklend_data"
    if isinstance(state, src.hashstack.HashstackState):
        return "hashstack_data"
    if isinstance(state, src.nostra.NostraState) and not isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "nostra_data"
    if isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "nostra_uncapped_data"
    raise ValueError


# TODO: make this an attribute of the State class?
def get_protocol(state: src.state.State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, src.zklend.ZkLendState):
        return "zkLend"
    if isinstance(state, src.hashstack.HashstackState):
        return "Hashstack"
    if isinstance(state, src.nostra.NostraState) and not isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "Nostra"
    if isinstance(state, src.nostra_uncapped.NostraUncappedState):
        return "Nostra uncapped"
    raise ValueError


# TODO: make this an attribute of the State class?
def get_supply_function_call_parameters(protocol: str, token: str) -> tuple[str, str]:
    if protocol == 'zkLend':
        return src.zklend.TOKEN_SETTINGS[token].protocol_token_address, 'felt_total_supply'
    if protocol in {'Nostra', 'Nostra uncapped'}:
        return src.nostra.TOKEN_SETTINGS[token].protocol_token_address, 'totalSupply'
    raise ValueError