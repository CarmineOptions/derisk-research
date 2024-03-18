from typing import Optional
import dataclasses

import pandas

import src.helpers
import src.nostra_alpha



# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#asset-contracts.
ADDRESSES_TO_TOKENS: dict[str, str] = {
    '0x01fecadfe7cda2487c66291f2970a629be8eecdcb006ba4e71d1428c2b7605c7': 'ETH',
    '0x002fc2d4b41cc1f03d185e6681cbd40cced61915d4891517a042658d61cba3b1': 'USDC',
    '0x0360f9786a6595137f84f2d6931aaec09ceec476a94a98dcad2bb092c6c06701': 'USDT',
    '0x022ccca3a16c9ef0df7d56cbdccd8c4a6f98356dfd11abc61a112483b242db90': 'DAI',
    '0x0735d0f09a4e8bf8a17005fa35061b5957dcaa56889fc75df9e94530ff6991ea': 'wBTC',
    '0x00ca44c79a77bcb186f8cdd1a0cd222cc258bebc3bec29a0a020ba20fdca40e9': 'wstETH',
    '0x0507eb06dd372cb5885d3aaf18b980c41cd3cd4691cfd3a820339a6c0cec2674': 'LORDS',
    '0x026c5994c2462770bbf940552c5824fb0e0920e2a8a5ce1180042da1b3e489db': 'STRK',
    '0x078a40c85846e3303bf7982289ca7def68297d4b609d5f588208ac553cff3a18': 'nstSTRK',
    '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893': 'ETH',
    '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4': 'USDC',
    '0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313': 'USDT',
    '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70': 'DAI',
    '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa': 'wBTC',
    '0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb': 'wstETH',
    '0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4': 'LORDS',
    '0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf': 'STRK',
    '0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5': 'nstSTRK',
    '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8': 'ETH',
    '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6': 'USDC',
    '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83': 'USDT', 
    '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9': 'DAI',
    '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c': 'wBTC',
    '0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a': 'wstETH',
    '0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd': 'LORDS',
    '0x07c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b': 'STRK',
    '0x067a34ff63ec38d0ccb2817c6d3f01e8b0c4792c77845feb43571092dcf5ebb5': 'nstSTRK',
    '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74': 'ETH',
    '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51': 'USDC',
    '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f': 'USDT',
    '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597': 'DAI',
    '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97': 'wBTC',
    '0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb': 'wstETH',
    '0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8': 'LORDS',
    '0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947': 'STRK',
    '0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b': 'nstSTRK',
}
# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#asset-contracts.
ADDRESSES_TO_EVENTS: dict[str, str] = {
    '0x01fecadfe7cda2487c66291f2970a629be8eecdcb006ba4e71d1428c2b7605c7': 'interest_bearing_deposit',
    '0x002fc2d4b41cc1f03d185e6681cbd40cced61915d4891517a042658d61cba3b1': 'interest_bearing_deposit',
    '0x0360f9786a6595137f84f2d6931aaec09ceec476a94a98dcad2bb092c6c06701': 'interest_bearing_deposit',
    '0x022ccca3a16c9ef0df7d56cbdccd8c4a6f98356dfd11abc61a112483b242db90': 'interest_bearing_deposit',
    '0x0735d0f09a4e8bf8a17005fa35061b5957dcaa56889fc75df9e94530ff6991ea': 'interest_bearing_deposit',
    '0x00ca44c79a77bcb186f8cdd1a0cd222cc258bebc3bec29a0a020ba20fdca40e9': 'interest_bearing_deposit',
    '0x0507eb06dd372cb5885d3aaf18b980c41cd3cd4691cfd3a820339a6c0cec2674': 'interest_bearing_deposit',
    '0x026c5994c2462770bbf940552c5824fb0e0920e2a8a5ce1180042da1b3e489db': 'interest_bearing_deposit',
    '0x078a40c85846e3303bf7982289ca7def68297d4b609d5f588208ac553cff3a18': 'interest_bearing_deposit',
    '0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893': 'non_interest_bearing_collateral',
    '0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4': 'non_interest_bearing_collateral',
    '0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313': 'non_interest_bearing_collateral',
    '0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70': 'non_interest_bearing_collateral',
    '0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa': 'non_interest_bearing_collateral',
    '0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb': 'non_interest_bearing_collateral',
    '0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4': 'non_interest_bearing_collateral',
    '0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf': 'non_interest_bearing_collateral',
    '0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5': 'non_interest_bearing_collateral',
    '0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8': 'interest_bearing_collateral',
    '0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6': 'interest_bearing_collateral',
    '0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83': 'interest_bearing_collateral', 
    '0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9': 'interest_bearing_collateral',
    '0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c': 'interest_bearing_collateral',
    '0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a': 'interest_bearing_collateral',
    '0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd': 'interest_bearing_collateral',
    '0x07c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b': 'interest_bearing_collateral',
    '0x067a34ff63ec38d0ccb2817c6d3f01e8b0c4792c77845feb43571092dcf5ebb5': 'interest_bearing_collateral',
    '0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74': 'debt',
    '0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51': 'debt',
    '0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f': 'debt',
    '0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597': 'debt',
    '0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97': 'debt',
    '0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb': 'debt',
    '0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8': 'debt',
    '0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947': 'debt',
    '0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b': 'debt',
}

# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#core-contracts.
INTEREST_RATE_MODEL_ADDRESS: str = '0x059a943ca214c10234b9a3b61c558ac20c005127d183b86a99a8f3c60a08b4ff'


@dataclasses.dataclass
class NostraMainnetSpecificTokenSettings:
    protocol_token_address: str


@dataclasses.dataclass
class TokenSettings(NostraMainnetSpecificTokenSettings, src.nostra_alpha.TokenSettings):
    pass


NOSTRA_MAINNET_SPECIFIC_TOKEN_SETTINGS: dict[str, NostraMainnetSpecificTokenSettings] = {
    "ETH": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x07170f54dd61ae85377f75131359e3f4a12677589bb7ec5d61f362915a5c0982",
    ),
    "wBTC": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x073132577e25b06937c64787089600886ede6202d085e6340242a5a32902e23e",
    ),
    "USDC": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x06eda767a143da12f70947192cd13ee0ccc077829002412570a88cd6539c1d85",
    ),
    "DAI": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x02b5fd690bb9b126e3517f7abfb9db038e6a69a068303d06cf500c49c1388e20",
    ),
    "USDT": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x06669cb476aa7e6a29c18b59b54f30b8bfcfbb8444f09e7bbb06c10895bf5d7b",
    ),
    "wstETH": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x07e2c010c0b381f347926d5a203da0335ef17aefee75a89292ef2b0f94924864",
    ),
    "LORDS": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x000d294e16a8d24c32eed65ea63757adde543d72bad4af3927f4c7c8969ff43d",
    ),
    "STRK": NostraMainnetSpecificTokenSettings(
        protocol_token_address="0x07c535ddb7bf3d3cb7c033bd1a4c3aac02927a4832da795606c0f3dbbc6efd17",
    ),
}
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    token: TokenSettings(
        # TODO: These can actually differ between Nostra Alpha and Nostra Mainnet.
        symbol=src.nostra_alpha.TOKEN_SETTINGS[token].symbol,
        decimal_factor=src.nostra_alpha.TOKEN_SETTINGS[token].decimal_factor,
        address=src.nostra_alpha.TOKEN_SETTINGS[token].address,
        collateral_factor=src.nostra_alpha.TOKEN_SETTINGS[token].collateral_factor,
        debt_factor=src.nostra_alpha.TOKEN_SETTINGS[token].debt_factor,
        liquidator_fee_beta=src.nostra_alpha.TOKEN_SETTINGS[token].liquidator_fee_beta,
        liquidator_fee_max=src.nostra_alpha.TOKEN_SETTINGS[token].liquidator_fee_max,
        protocol_fee=src.nostra_alpha.TOKEN_SETTINGS[token].protocol_fee,
        protocol_token_address=NOSTRA_MAINNET_SPECIFIC_TOKEN_SETTINGS[token].protocol_token_address,
    )
    for token in src.nostra_alpha.TOKEN_SETTINGS
}



def get_events(start_block_number: int = 0) -> pandas.DataFrame:
    user_events = src.helpers.get_events(
        addresses = tuple(x for x in ADDRESSES_TO_TOKENS if ADDRESSES_TO_EVENTS[x] != 'interest_bearing_deposit'),
        event_names = (
            'Burn', 
            'Mint',
            'nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn',
            'nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint',
        ),
        start_block_number = start_block_number,
    )
    interest_rate_events = src.helpers.get_events(
        addresses = (INTEREST_RATE_MODEL_ADDRESS, ''),
        event_names = ('InterestStateUpdated', ''),
        start_block_number = start_block_number,
    )
    events = pandas.concat([user_events, interest_rate_events])
    events.sort_values(['block_number', 'id'], inplace = True)
    return events


class NostraMainnetLoanEntity(src.nostra_alpha.NostraAlphaLoanEntity):
    """
    A class that describes the Nostra Mainnet loan entity. Compared to `src.nostra_alpha.NostraAlphaLoanEntity`, it 
    only implements its own `TOKEN_SETTINGS`.
    """

    TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS


class NostraMainnetState(src.nostra_alpha.NostraAlphaState):
    """
    A class that describes the state of all Nostra Mainnet loan entities. All methods for correct processing of every 
    relevant event are implemented in `src.nostra_alpha.NostraAlphaState`.
    """

    ADDRESSES_TO_TOKENS: dict[str, str] = ADDRESSES_TO_TOKENS
    ADDRESSES_TO_EVENTS: dict[str, str] = ADDRESSES_TO_EVENTS
    INTEREST_RATE_MODEL_ADDRESS: str = INTEREST_RATE_MODEL_ADDRESS
    # TODO: This seems to be a magical address.
    IGNORE_USER: str = '0x5fc7053cca20fcb38550d7554c84fa6870e2b9e7ebd66398a67697ba440f12b'

    def __init__(
        self,
        verbose_user: Optional[str] = None,
    ) -> None:
        super().__init__(
            loan_entity_class=NostraMainnetLoanEntity,
            verbose_user=verbose_user,
        )