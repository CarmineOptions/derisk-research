from typing import Optional
import dataclasses

import pandas

import src.helpers
import src.nostra



# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#asset-contracts.
ADDRESSES_TO_TOKENS: dict[str, str] = {
    '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893': 'ETH',
    '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4': 'USDC',
    '0x057717edc5b1e56743e8153be626729eb0690b882466ef0cbedc8a28bb4973b1': 'USDT',
    '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70': 'DAI',
    '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa': 'wBTC',
    '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8': 'ETH',
    '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6': 'USDC',
    '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83': 'USDT', 
    '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9': 'DAI',
    '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c': 'wBTC',
    '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74': 'ETH',
    '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51': 'USDC',
    '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f': 'USDT',
    '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597': 'DAI',
    '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97': 'wBTC',
}
# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#asset-contracts.
ADDRESSES_TO_EVENTS: dict[str, str] = {
    '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893': 'non_interest_bearing_collateral',
    '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4': 'non_interest_bearing_collateral',
    '0x057717edc5b1e56743e8153be626729eb0690b882466ef0cbedc8a28bb4973b1': 'non_interest_bearing_collateral',
    '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70': 'non_interest_bearing_collateral',
    '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa': 'non_interest_bearing_collateral',
    '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8': 'interest_bearing_collateral',
    '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6': 'interest_bearing_collateral',
    '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83': 'interest_bearing_collateral', 
    '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9': 'interest_bearing_collateral',
    '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c': 'interest_bearing_collateral',
    '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74': 'debt',
    '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51': 'debt',
    '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f': 'debt',
    '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597': 'debt',
    '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97': 'debt',
}

# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#core-contracts.
INTEREST_RATE_MODEL_ADDRESS: str = '0x059a943ca214c10234b9a3b61c558ac20c005127d183b86a99a8f3c60a08b4ff'


@dataclasses.dataclass
class NostraUncappedSpecificTokenSettings:
    protocol_token_address: str


@dataclasses.dataclass
class TokenSettings(NostraUncappedSpecificTokenSettings, src.nostra.TokenSettings):
    pass


NOSTRA_UNCAPPED_SPECIFIC_TOKEN_SETTINGS: dict[str, NostraUncappedSpecificTokenSettings] = {
    "ETH": NostraUncappedSpecificTokenSettings(
        protocol_token_address="0x07170f54dd61ae85377f75131359e3f4a12677589bb7ec5d61f362915a5c0982",
    ),
    "wBTC": NostraUncappedSpecificTokenSettings(
        protocol_token_address="0x073132577e25b06937c64787089600886ede6202d085e6340242a5a32902e23e",
    ),
    "USDC": NostraUncappedSpecificTokenSettings(
        protocol_token_address="0x06eda767a143da12f70947192cd13ee0ccc077829002412570a88cd6539c1d85",
    ),
    "DAI": NostraUncappedSpecificTokenSettings(
        protocol_token_address="0x02b5fd690bb9b126e3517f7abfb9db038e6a69a068303d06cf500c49c1388e20",
    ),
    "USDT": NostraUncappedSpecificTokenSettings(
        protocol_token_address="0x06669cb476aa7e6a29c18b59b54f30b8bfcfbb8444f09e7bbb06c10895bf5d7b",
    ),
    # TODO: Add wstETH.
    "wstETH": NostraUncappedSpecificTokenSettings(protocol_token_address=""),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        symbol=src.nostra.TOKEN_SETTINGS[token].symbol,
        decimal_factor=src.nostra.TOKEN_SETTINGS[token].decimal_factor,
        address=src.nostra.TOKEN_SETTINGS[token].address,
        collateral_factor=src.nostra.TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=src.nostra.TOKEN_SETTINGS[token].debt_factor,
        liquidator_fee_beta=src.nostra.TOKEN_SETTINGS[token].liquidator_fee_beta,
        liquidator_fee_max=src.nostra.TOKEN_SETTINGS[token].liquidator_fee_max,
        protocol_fee=src.nostra.TOKEN_SETTINGS[token].protocol_fee,
        protocol_token_address=NOSTRA_UNCAPPED_SPECIFIC_TOKEN_SETTINGS[token].protocol_token_address,
    )
    for token in src.nostra.TOKEN_SETTINGS
}



def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    user_events = src.helpers.get_events(
        adresses = tuple(ADDRESSES_TO_TOKENS),
        events = ('Burn', 'Mint'),
        start_block_number = start_block_number,
    )
    interest_rate_events = src.helpers.get_events(
        adresses = (INTEREST_RATE_MODEL_ADDRESS, ''),
        events = ('InterestStateUpdated', ''),
        start_block_number = start_block_number,
    )
    events = pandas.concat([user_events, interest_rate_events])
    events.sort_values(['block_number', 'id'], inplace = True)
    return events


class NostraUncappedLoanEntity(src.nostra.NostraLoanEntity):
    """
    A class that describes the Nostra Uncapped loan entity. Compared to `src.nostra.NostraLoanEntity`, it only 
    implements its own `TOKEN_SETTINGS`.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS


class NostraUncappedState(src.nostra.NostraState):
    """
    A class that describes the state of all Nostra uncapped loan entities. All methods for correct processing of every 
    relevant event are implemented in `src.nostra.NostraState`.
    """

    ADDRESSES_TO_TOKENS = ADDRESSES_TO_TOKENS
    ADDRESSES_TO_EVENTS = ADDRESSES_TO_EVENTS
    INTEREST_RATE_MODEL_ADDRESS = INTEREST_RATE_MODEL_ADDRESS
    # TODO: This seems to be a magical address.
    IGNORE_USER: str = '0x5fc7053cca20fcb38550d7554c84fa6870e2b9e7ebd66398a67697ba440f12b'

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=NostraUncappedLoanEntity,
            verbose_user=verbose_user,
        )