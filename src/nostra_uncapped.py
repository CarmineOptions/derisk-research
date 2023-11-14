from typing import Dict

import pandas

import src.helpers
import src.nostra



ADDRESSES_TO_TOKENS: Dict[str, str] = {
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
ADDRESSES_TO_EVENTS: Dict[str, str] = {
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

INTEREST_RATE_MODEL_ADDRESS: str = '0x059a943ca214c10234b9a3b61c558ac20c005127d183b86a99a8f3c60a08b4ff'



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


class NostraUncappedState(src.nostra.NostraState):
    """
    A class that describes the state of all Nostra uncapped loan entities. It implements a method for correct 
    processing of every relevant event.
    """

    ADDRESSES_TO_TOKENS = ADDRESSES_TO_TOKENS
    ADDRESSES_TO_EVENTS = ADDRESSES_TO_EVENTS
    INTEREST_RATE_MODEL_ADDRESS = INTEREST_RATE_MODEL_ADDRESS
    # TODO: This seems to be a magical address.
    IGNORE_USER: str = '0x5fc7053cca20fcb38550d7554c84fa6870e2b9e7ebd66398a67697ba440f12b'