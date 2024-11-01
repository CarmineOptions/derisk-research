""" This module contains constants for the data handler """
from dataclasses import dataclass, field
from enum import Enum
from typing import Set


# Temporary solution.
# TODO remove it when all protocols with interest rate models will be available
class AvailableProtocolID(Enum):
    """class docstring"""
    # nostra protocols
    NOSTRA_ALPHA: str = "Nostra_alpha"
    NOSTRA_MAINNET: str = "Nostra_mainnet"
    # zkLend protocol
    ZKLEND: str = "zkLend"


@dataclass(frozen=True)
class ProtocolAddresses:
    """
    This class contains the addresses of the contracts that are used
    """

    ZKLEND_MARKET_ADDRESSES: str = field(
        default_factory=lambda: "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"
    )
    HASHSTACK_V0_ADDRESSES: Set[str] = field(
        default_factory=lambda:
        {"0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e"}
    )
    HASHSTACK_V1_R_TOKENS: Set[str] = field(
        default_factory=lambda: {
            "0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e",  # ETH
            "0x03bcecd40212e9b91d92bbe25bb3643ad93f0d230d93237c675f46fac5187e8c",  # USDC
            "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21",  # USDT
            "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f",  # DAI
            "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef",  # wBTC
            "0x07514ee6fa12f300ce293c60d60ecce0704314defdb137301dae78a7e5abbdd7",  # STRK
        }
    )
    HASHSTACK_V1_D_TOKENS: Set[str] = field(
        default_factory=lambda: {
            "0x01ef7f9f8bf01678dc6d27e2c26fb7e8eac3812a24752e6a1d6a49d153bec9f3",  # ETH
            "0x021d8d8519f5464ec63c6b9a80a5229c5ddeed57ecded4c8a9dfc34e31b49990",  # USDC
            "0x012b8185e237dd0340340faeb3351dbe53f8a42f5a9bf974ddf90ced56e301c7",  # USDT
            "0x07eeed99c095f83716e465e2c52a3ec8f47b323041ddc4f97778ac0393b7f358",  # DAI
            "0x02614c784267d2026042ab98588f90efbffaade8982567e93530db4ed41201cf",  # wBTC
            "0x01bdbaaa456c7d6bbba9ff740af3cfcd40bec0e85cd5cefc3fbb05a552fd14df",  # STRK
        }
    )
    NOSTRA_ALPHA_ADDRESSES: Set[str] = field(
        default_factory=lambda: {
            "0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453",
            "0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833",
            "0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601",
            "0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17",
            "0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53",
            "0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6",
            "0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e",
            "0x055ba2baf189b98c59f6951a584a3a7d7d6ff2c4ef88639794e739557e1876f0",
            "0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58",
            "0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9",
            "0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5",
            "0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a",
            "0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6",
            "0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb",
            "0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7",
        }
    )
    NOSTRA_MAINNET_ADDRESSES: Set[str] = field(
        default_factory=lambda: {
            # addresses which using for `interest_bearing_deposit` event
            # "0x01fecadfe7cda2487c66291f2970a629be8eecdcb006ba4e71d1428c2b7605c7",
            # "0x002fc2d4b41cc1f03d185e6681cbd40cced61915d4891517a042658d61cba3b1",
            # "0x0360f9786a6595137f84f2d6931aaec09ceec476a94a98dcad2bb092c6c06701",
            # "0x022ccca3a16c9ef0df7d56cbdccd8c4a6f98356dfd11abc61a112483b242db90",
            # "0x0735d0f09a4e8bf8a17005fa35061b5957dcaa56889fc75df9e94530ff6991ea",
            # "0x00ca44c79a77bcb186f8cdd1a0cd222cc258bebc3bec29a0a020ba20fdca40e9",
            # "0x0507eb06dd372cb5885d3aaf18b980c41cd3cd4691cfd3a820339a6c0cec2674",
            # "0x026c5994c2462770bbf940552c5824fb0e0920e2a8a5ce1180042da1b3e489db",
            # "0x078a40c85846e3303bf7982289ca7def68297d4b609d5f588208ac553cff3a18",
            "0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893",
            "0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4",
            "0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313",
            "0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70",
            "0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa",
            "0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb",
            "0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4",
            "0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf",
            "0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5",
            "0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8",
            "0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6",
            "0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83",
            "0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9",
            "0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c",
            "0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a",
            "0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd",
            "0x07c2e1e733f28daa23e78be3a4f6c724c0ab06af65f6a95b5e0545215f1abc1b",
            "0x067a34ff63ec38d0ccb2817c6d3f01e8b0c4792c77845feb43571092dcf5ebb5",
            "0x00ba3037d968790ac486f70acaa9a1cab10cf5843bb85c986624b4d0e5a82e74",
            "0x063d69ae657bd2f40337c39bf35a870ac27ddf91e6623c2f52529db4c1619a51",
            "0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f",
            "0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597",
            "0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97",
            "0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb",
            "0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8",
            "0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947",
            "0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b",
        }
    )


NOSTRA_EVENTS_MAPPING = {
    "Mint":
    "process_debt_mint_event",
    "Burn":
    "process_debt_burn_event",
    "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Burn":
    "process_debt_burn_event",
    "nostra::core::tokenization::lib::nostra_token::NostraTokenComponent::Mint":
    "process_debt_mint_event",
}

FIRST_RUNNING_MAPPING = {
    # zkLend
    "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05": 48668,
    # Hashstack_v0
    "0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e": 21000,
    # Hashstack_v1_r
    "0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e": 268062,  # ETH
    "0x03bcecd40212e9b91d92bbe25bb3643ad93f0d230d93237c675f46fac5187e8c": 268067,  # USDC
    "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21": 268064,  # USDT
    "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f": 268070,  # DAI
    # Hashstack_v1_d
    "0x01ef7f9f8bf01678dc6d27e2c26fb7e8eac3812a24752e6a1d6a49d153bec9f3": 268063,  # ETH
    "0x021d8d8519f5464ec63c6b9a80a5229c5ddeed57ecded4c8a9dfc34e31b49990": 268068,  # USDC
    "0x012b8185e237dd0340340faeb3351dbe53f8a42f5a9bf974ddf90ced56e301c7": 268065,  # USDT
    "0x07eeed99c095f83716e465e2c52a3ec8f47b323041ddc4f97778ac0393b7f358": 268071,  # DAI
    "0x02614c784267d2026042ab98588f90efbffaade8982567e93530db4ed41201cf": 268060,  # wBTC
    # Nostra_alpha
    "0x0553cea5d1dc0e0157ffcd36a51a0ced717efdadd5ef1b4644352bb45bd35453": 10854,
    "0x047e794d7c49c49fd2104a724cfa69a92c5a4b50a5753163802617394e973833": 10892,
    "0x003cd2066f3c8b4677741b39db13acebba843bbbaa73d657412102ab4fd98601": 10895,
    "0x04403e420521e7a4ca0dc5192af81ca0bb36de343564a9495e11c8d9ba6e9d17": 10889,
    "0x06b59e2a746e141f90ec8b6e88e695265567ab3bdcf27059b4a15c89b0b7bd53": 10852,
    "0x070f8a4fcd75190661ca09a7300b7c93fab93971b67ea712c664d7948a8a54c6": 10853,
    "0x029959a546dda754dc823a7b8aa65862c5825faeaaf7938741d8ca6bfdc69e4e": 10891,
    "0x01ac55cabf2b79cf39b17ba0b43540a64205781c4b7850e881014aea6f89be58": 10889,
    "0x00687b5d9e591844169bc6ad7d7256c4867a10cee6599625b9d78ea17a7caef9": 10851,
    "0x040b091cb020d91f4a4b34396946b4d4e2a450dbd9410432ebdbfe10e55ee5e5": 10853,
    "0x03b6058a9f6029b519bc72b2cc31bcb93ca704d0ab79fec2ae5d43f79ac07f7a": 10891,
    "0x065c6c7119b738247583286021ea05acc6417aa86d391dcdda21843c1fc6e9c6": 10893,
    "0x0362b4455f5f4cc108a5a1ab1fd2cc6c4f0c70597abb541a99cf2734435ec9cb": 10854,
    "0x075b0d87aca8dee25df35cdc39a82b406168fa23a76fc3f03abbfdc6620bb6d7": 10851,
    # Nostra_mainnet
    "0x044debfe17e4d9a5a1e226dabaf286e72c9cc36abbe71c5b847e669da4503893": 165334,
    "0x05f296e1b9f4cf1ab452c218e72e02a8713cee98921dad2d3b5706235e128ee4": 168359,
    "0x0514bd7ee8c97d4286bd481c54aa0793e43edbfb7e1ab9784c4b30469dcf9313": 168369,
    "0x005c4676bcb21454659479b3cd0129884d914df9c9b922c1c649696d2e058d70": 166394,
    "0x036b68238f3a90639d062669fdec08c4d0bdd09826b1b6d24ef49de6d8141eaa": 166444,
    "0x05eb6de9c7461b3270d029f00046c8a10d27d4f4a4c931a4ea9769c72ef4edbb": 548292,
    "0x02530a305dd3d92aad5cf97e373a3d07577f6c859337fb0444b9e851ee4a2dd4": 548354,
    "0x040f5a6b7a6d3c472c12ca31ae6250b462c6d35bbdae17bd52f6c6ca065e30cf": 548438,
    "0x0142af5b6c97f02cac9c91be1ea9895d855c5842825cb2180673796e54d73dc5": 165330,
    "0x057146f6409deb4c9fa12866915dd952aa07c1eb2752e451d7f3b042086bdeb8": 165330,
    "0x05dcd26c25d9d8fd9fc860038dcb6e4d835e524eb8a85213a8cda5b7fff845f6": 168358,
    "0x0453c4c996f1047d9370f824d68145bd5e7ce12d00437140ad02181e1d11dc83": 168365,
    "0x04f18ffc850cdfa223a530d7246d3c6fc12a5969e0aa5d4a88f470f5fe6c46e9": 166368,
    "0x05b7d301fa769274f20e89222169c0fad4d846c366440afc160aafadd6f88f0c": 166443,
    "0x009377fdde350e01e0397820ea83ed3b4f05df30bfb8cf8055d62cafa1b2106a": 548418,
    "0x0739760bce37f89b6c1e6b1198bb8dc7166b8cf21509032894f912c9d5de9cbd": 548364,
    "0x024e9b0d6bc79e111e6872bb1ada2a874c25712cf08dfc5bcf0de008a7cca55f": 168364,
    "0x066037c083c33330a8460a65e4748ceec275bbf5f28aa71b686cbc0010e12597": 166354,
    "0x0491480f21299223b9ce770f23a2c383437f9fbf57abc2ac952e9af8cdb12c97": 166442,
    "0x0348cc417fc877a7868a66510e8e0d0f3f351f5e6b0886a86b652fcb30a3d1fb": 548320,
    "0x035778d24792bbebcf7651146896df5f787641af9e2a3db06480a637fbc9fff8": 548359,
    "0x001258eae3eae5002125bebf062d611a772e8aea3a1879b64a19f363ebd00947": 548440,
    "0x0292be6baee291a148006db984f200dbdb34b12fb2136c70bfe88649c12d934b": 168364,
}

TOKEN_MAPPING = {
    "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": "ETH",
    "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": "USDC",
    "0x68f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8": "USDT",
    "0xda114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3": "DAI",
    "0x3fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac": "wBTC",
    "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d": "STRK",
    "0x719b5092403233201aa822ce928bd4b551d0cdb071a724edd7dc5e5f57b7f34": "UNO",
    "0x585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34": "ZEND",
    "0x42b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2": "wstETH",
    "0x124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49": "LORDS",
}
