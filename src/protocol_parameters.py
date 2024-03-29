import src.hashstack_v0
import src.hashstack_v1
import src.nostra_alpha
import src.nostra_mainnet
import src.zklend



# TODO: make this an attribute of the State class? Or get it from the name of the protocol?
def get_directory(state: src.state.State) -> str:
    # TODO: Improve the inference.
    if isinstance(state, src.zklend.ZkLendState):
        return "zklend_data"
    if isinstance(state, src.hashstack_v0.HashstackV0State):
        return "hashstack_v0_data"
    if isinstance(state, src.hashstack_v1.HashstackV1State):
        return "hashstack_v1_data"
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
    if isinstance(state, src.hashstack_v0.HashstackV0State):
        return "Hashstack V0"
    if isinstance(state, src.hashstack_v1.HashstackV1State):
        return "Hashstack V1"
    if isinstance(state, src.nostra_alpha.NostraAlphaState) and not isinstance(state, src.nostra_mainnet.NostraMainnetState):
        return "Nostra Alpha"
    if isinstance(state, src.nostra_mainnet.NostraMainnetState):
        return "Nostra Mainnet"
    raise ValueError


# TODO: make this an attribute of the State class?
def get_supply_function_call_parameters(protocol: str, token: str) -> tuple[list[str], str]:
    if protocol == 'zkLend':
        return [src.zklend.TOKEN_SETTINGS[token].protocol_token_address], 'felt_total_supply'
    if protocol == 'Nostra Alpha':
        token_addresses = [
            address
            for address, nostra_token
            in src.nostra_alpha.ADDRESSES_TO_TOKENS.items()
            if (
                nostra_token == token
                and src.nostra_alpha.ADDRESSES_TO_EVENTS[address] in {
                    'interest_bearing_deposit',
                    'interest_bearing_collateral',
                }
            )
        ]
        return token_addresses, 'totalSupply'
    if protocol == 'Nostra Mainnet':
        token_addresses = [
            address
            for address, nostra_token
            in src.nostra_mainnet.ADDRESSES_TO_TOKENS.items()
            if (
                nostra_token == token
                and src.nostra_mainnet.ADDRESSES_TO_EVENTS[address] in {
                    'interest_bearing_deposit',
                    'interest_bearing_collateral',
                }
            )
        ]
        return token_addresses, 'totalSupply'
    raise ValueError