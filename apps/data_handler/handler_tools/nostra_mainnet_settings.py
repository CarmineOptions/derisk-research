"""Settings for the Nostra mainnet."""
# Source: https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#core-contracts.
NOSTRA_MAINNET_INTEREST_RATE_MODEL_ADDRESS: str = (
    "0x059a943ca214c10234b9a3b61c558ac20c005127d183b86a99a8f3c60a08b4ff"
)

# TODO: add missing contracts to the db
# The commented addresses are non-collateral deposits which might be useful later. Source:
# https://docs.nostra.finance/lend/deployed-contracts/lend-mainnet#asset-contracts.
NOSTRA_MAINNET_TOKEN_ADDRESSES: list[str] = [
    # '0x0735d0f09a4e8bf8a17005fa35061b5957dcaa56889fc75df9e94530ff6991ea',  # iWBTC
    "0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c",  # iWBTC-c
    # '0x073132577e25b06937c64787089600886ede6202d085e6340242a5a32902e23e',  # nWBTC
    "0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa",  # nWBTC-c
    "0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97",  # dWBTC
    # '0x01fecadfe7cda2487c66291f2970a629be8eecdcb006ba4e71d1428c2b7605c7',  # iETH
    "0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8",  # iETH-c
    # '0x07170f54dd61ae85377f75131359e3f4a12677589bb7ec5d61f362915a5c0982',  # nETH
    "0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893",  # nETH-c
    "0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74",  # dETH
    # '0x002fc2d4b41cc1f03d185e6681cbd40cced61915d4891517a042658d61cba3b1',  # iUSDC
    "0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6",  # iUSDC-c
    # '0x06eda767a143da12f70947192cd13ee0ccc077829002412570a88cd6539c1d85',  # nUSDC
    "0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4",  # nUSDC-c
    "0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51",  # dUSDC
    # '0x022ccca3a16c9ef0df7d56cbdccd8c4a6f98356dfd11abc61a112483b242db90',  # iDAI
    "0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9",  # iDAI-c
    # '0x02b5fd690bb9b126e3517f7abfb9db038e6a69a068303d06cf500c49c1388e20',  # nDAI
    "0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70",  # nDAI-c
    "0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597",  # dDAI
    # '0x0360f9786a6595137f84f2d6931aaec09ceec476a94a98dcad2bb092c6c06701',  # iUSDT
    "0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83",  # iUSDT-c
    # '0x06669cb476aa7e6a29c18b59b54f30b8bfcfbb8444f09e7bbb06c10895bf5d7b',  # nUSDT
    "0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313",  # nUSDT-c
    "0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f",  # dUSDT
    # '0x00ca44c79a77bcb186f8cdd1a0cd222cc258bebc3bec29a0a020ba20fdca40e9',  # iwstETH
    "0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a",  # iwstETH-c
    # '0x07e2c010c0b381f347926d5a203da0335ef17aefee75a89292ef2b0f94924864',  # nwstETH
    "0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb",  # nwstETH-c
    "0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb",  # dwstETH
    # '0x0507eb06dd372cb5885d3aaf18b980c41cd3cd4691cfd3a820339a6c0cec2674',  # iLORDS
    "0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd",  # iLORDS-c
    # '0x000d294e16a8d24c32eed65ea63757adde543d72bad4af3927f4c7c8969ff43d',  # nLORDS
    "0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4",  # nLORDS-c
    "0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8",  # dLORDS
    # '0x026c5994c2462770bbf940552c5824fb0e0920e2a8a5ce1180042da1b3e489db',  # iSTRK
    "0x07c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b",  # iSTRK-c
    # '0x07c535ddb7bf3d3cb7c033bd1a4c3aac02927a4832da795606c0f3dbbc6efd17',  # nSTRK
    "0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf",  # nSTRK-c
    "0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947",  # dSTRK
    # '0x078a40c85846e3303bf7982289ca7def68297d4b609d5f588208ac553cff3a18',  # instSTRK
    "0x067a34ff63ec38d0ccb2817c6d3f01e8b0c4792c77845feb43571092dcf5ebb5",  # instSTRK-c
    # '0x04b11c750ae92c13fdcbe514f9c47ba6f8266c81014501baa8346d3b8ba55342',  # nnstSTRK
    "0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5",  # nnstSTRK-c
    "0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b",  # dnstSTRK
    # '0x01325caf7c91ee415b8df721fb952fa88486a0fc250063eafddd5d3c67867ce7',  # iUNO
    "0x02a3a9d7bcecc6d3121e3b6180b73c7e8f4c5f81c35a90c8dd457a70a842b723",  # iUNO-c
    # '0x06757ef9960c5bc711d1ba7f7a3bff44a45ba9e28f2ac0cc63ee957e6cada8ea',  # nUNO
    "0x07d717fb27c9856ea10068d864465a2a8f9f669f4f78013967de06149c09b9af",  # nUNO-c
    "0x04b036839a8769c04144cc47415c64b083a2b26e4a7daa53c07f6042a0d35792",  # dUNO
    # '0x02589fc11f60f21af6a1dda3aeb7a44305c552928af122f2834d1c3b1a7aa626',  # iNSTR
    "0x046ab56ec0c6a6d42384251c97e9331aa75eb693e05ed8823e2df4de5713e9a4",  # iNSTR-c
    # '0x02b674ffda238279de5550d6f996bf717228d316555f07a77ef0a082d925b782',  # nNSTR
    "0x06f8ad459c712873993e9ffb9013a469248343c3d361e4d91a8cac6f98575834",  # nNSTR-c
    "0x03e0576565c1b51fcac3b402eb002447f21e97abb5da7011c0a2e0b465136814",  # dNSTR
    # '0x065bde349f553cf4bdd873e54cd48317eda0542764ebe5ba46984cedd940a5e4',  # iDAI V2
    # '0x0184dd6328115c2d5f038792e427f3d81d9552e40dd675e013ccbf74ba50b979',  # nDAI V2
    "0x06726ec97bae4e28efa8993a8e0853bd4bad0bd71de44c23a1cd651b026b00e7",  # dDAI V2
]

NOSTRA_MAINNET_CDP_MANAGER_ADDRESS: str = (
    "0x073f6addc9339de9822cab4dac8c9431779c09077f02ba7bc36904ea342dd9eb"
)

# This seems to be a magical address, it's first event is a withdrawal.
# Ignore it's loan state changes.
NOSTRA_MAINNET_DEFERRED_BATCH_CALL_ADAPTER_ADDRESS: str = (
    "0x05fc7053cca20fcb38550d7554c84fa6870e2b9e7ebd66398a67697ba440f12b"
)

# Keys are tuples of event types and names, values are names of the
# respective methods that process the given event.
NOSTRA_MAINNET_EVENTS_TO_METHODS = {
    ("collateral", "Transfer"):
    "process_collateral_transfer_event",
    (
        "collateral",
        "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer",
    ):
    "process_collateral_transfer_event",
    (
        "collateral",
        "openzeppelin::token::erc20::erc20::ERC20Component::Transfer",
    ):
    "process_collateral_transfer_event",
    (
        "collateral",
        "nstr::openzeppelin::token::erc20_v070::erc20::ERC20Starkgate::Transfer",
    ):
    "process_collateral_transfer_event",
    ("collateral", "Mint"):
    "process_collateral_mint_event",
    (
        "collateral",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint",
    ):
    "process_collateral_mint_event",
    ("collateral", "Burn"):
    "process_collateral_burn_event",
    (
        "collateral",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn",
    ):
    "process_collateral_burn_event",
    ("debt", "Transfer"):
    "process_debt_transfer_event",
    (
        "debt",
        "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer",
    ):
    "process_debt_transfer_event",
    (
        "debt",
        "openzeppelin::token::erc20::erc20::ERC20Component::Transfer",
    ):
    "process_debt_transfer_event",
    (
        "debt",
        "nstr::openzeppelin::token::erc20_v070::erc20::ERC20Starkgate::Transfer",
    ):
    "process_debt_transfer_event",
    ("debt", "Mint"):
    "process_debt_mint_event",
    (
        "debt",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint",
    ):
    "process_debt_mint_event",
    ("debt", "Burn"):
    "process_debt_burn_event",
    (
        "debt",
        "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn",
    ):
    "process_debt_burn_event",
}

# Keys are event names, values denote the order in which the given events should be processed.
NOSTRA_MAINNET_EVENTS_TO_ORDER: dict[str, str] = {
    "InterestStateUpdated":
    0,
    "nostra::lending::interest_rate_model::interest_rate_model::"
    "InterestRateModel::InterestStateUpdated":
    1,
    "Transfer":
    2,
    "openzeppelin::token::erc20_v070::erc20::ERC20::Transfer":
    3,
    "openzeppelin::token::erc20::erc20::ERC20Component::Transfer":
    4,
    "nstr::openzeppelin::token::erc20_v070::erc20::ERC20Starkgate::Transfer":
    5,
    "Burn":
    6,
    "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn":
    7,
    "Mint":
    8,
    "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint":
    9,
}

NOSTRA_MAINNET_ADDRESSES_TO_EVENTS: dict[str, str] = {
    "0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893":
    "non_interest_bearing_collateral",
    "0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4":
    "non_interest_bearing_collateral",
    "0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313":
    "non_interest_bearing_collateral",
    "0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70":
    "non_interest_bearing_collateral",
    "0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa":
    "non_interest_bearing_collateral",
    "0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb":
    "non_interest_bearing_collateral",
    "0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4":
    "non_interest_bearing_collateral",
    "0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf":
    "non_interest_bearing_collateral",
    "0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5":
    "non_interest_bearing_collateral",
    "0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8":
    "interest_bearing_collateral",
    "0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6":
    "interest_bearing_collateral",
    "0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83":
    "interest_bearing_collateral",
    "0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9":
    "interest_bearing_collateral",
    "0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c":
    "interest_bearing_collateral",
    "0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a":
    "interest_bearing_collateral",
    "0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd":
    "interest_bearing_collateral",
    "0x07c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b":
    "interest_bearing_collateral",
    "0x067a34ff63ec38d0ccb2817c6d3f01e8b0c4792c77845feb43571092dcf5ebb5":
    "interest_bearing_collateral",
    "0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74": "debt",
    "0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51": "debt",
    "0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f": "debt",
    "0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597": "debt",
    "0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97": "debt",
    "0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb": "debt",
    "0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8": "debt",
    "0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947": "debt",
    "0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b": "debt",
}
