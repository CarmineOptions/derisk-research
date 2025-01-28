""" This module contains the constants used in the system. """

from decimal import Decimal
from enum import Enum
from typing import List, Union

from shared.custom_types import TokenSettings

ZKLEND = "zkLend"
NOSTRA_ALPHA = "Nostra Alpha"
NOSTRA_MAINNET = "Nostra Mainnet"
NULL_CHAR = "\x00"
GS_BUCKET_NAME = "derisk-persistent-state/v3"

TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "ETH": TokenSettings(
        symbol="ETH",
        decimal_factor=Decimal("1e18"),
        address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "wBTC": TokenSettings(
        symbol="wBTC",
        decimal_factor=Decimal("1e8"),
        address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    ),
    "USDC": TokenSettings(
        symbol="USDC",
        decimal_factor=Decimal("1e6"),
        address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    # FIXME Uncomment when DAI is added correct address
    # "DAI": TokenSettings(
    #     symbol="DAI",
    #     decimal_factor=Decimal("1e18"),
    #     address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    # ),
    "USDT": TokenSettings(
        symbol="USDT",
        decimal_factor=Decimal("1e6"),
        address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "wstETH": TokenSettings(
        symbol="wstETH",
        decimal_factor=Decimal("1e18"),
        address="0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",
    ),
    "LORDS": TokenSettings(
        symbol="LORDS",
        decimal_factor=Decimal("1e18"),
        address="0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",
    ),
    "STRK": TokenSettings(
        symbol="STRK",
        decimal_factor=Decimal("1e18"),
        address="0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    ),
}
POOL_MAPPING: dict[str, dict[str, Union[List, str]]] = {
    "ETH_USDC": {
        "base_token": "ETH",
        "quote_token": "USDC",
        "addresses": [
            "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",  # jediswap
            "0x030615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f",  # sithswap
            "0x000023c72abdf49dffc85ae3ede714f2168ad384cc67d08524732acea90df325",  # 10kswap
        ],
        "myswap_id": 1,
    },
    "DAI_ETH": {
        "base_token": "DAI",
        "quote_token": "ETH",
        "addresses": [
            "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",  # jediswap
            "0x0032ebb8e68553620b97b308684babf606d9556d5c0a652450c32e85f40d000d",  # sithswap
            "0x017e9e62c04b50800d7c59454754fe31a2193c9c3c6c92c093f2ab0faadf8c87",  # 10kswap
        ],
        "myswap_id": 2,
    },
    "ETH_USDT": {
        "base_token": "ETH",
        "quote_token": "USDT",
        "addresses": [
            "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",  # jediswap
            "0x00691fa7f66d63dc8c89ff4e77732fff5133f282e7dbd41813273692cc595516",  # sithswap
            "0x05900cfa2b50d53b097cb305d54e249e31f24f881885aae5639b0cd6af4ed298",  # 10kswap
        ],
        "myswap_id": 4,
    },
    "wBTC_ETH": {
        "base_token": "wBTC",
        "quote_token": "ETH",
        "addresses": [
            "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",  # jediswap
            "0x02a6e0ecda844736c4803a385fb1372eff458c365d2325c7d4e08032c7a908f3",  # 10kswap
        ],
        "myswap_id": None,
    },
    "wBTC_USDT": {
        "base_token": "wBTC",
        "quote_token": "USDT",
        "addresses": [
            "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",  # jediswap
            "0x050031010bcee2f43575b3afe197878e064e1a03c12f2ff437f29a2710e0b6ef",  # 10kswap
        ],
        "myswap_id": None,
    },
    "DAI_wBTC": {
        "base_token": "DAI",
        "quote_token": "wBTC",
        "addresses": [
            "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",  # jediswap
            "0x00f9d8f827734f5fd54571f0e78398033a3c1f1074a471cd4623f2aa45163718",  # 10kswap
        ],
        "myswap_id": None,
    },
    "DAI_USDC": {
        "base_token": "DAI",
        "quote_token": "USDC",
        "addresses": [
            "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",  # jediswap
            "0x015e9cd2d4d6b4bb9f1124688b1e6bc19b4ff877a01011d28c25c9ee918e83e5",  # sithswap
            "0x02e767b996c8d4594c73317bb102c2018b9036aee8eed08ace5f45b3568b94e5",  # 10kswap
        ],
        "myswap_id": 6,
    },
    "DAI_USDT": {
        "base_token": "DAI",
        "quote_token": "USDT",
        "addresses": [
            "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",  # jediswap
            "0x041d52e15e82b003bf0ad52ca58393c87abef3e00f1bf69682fd4162d5773f8f",  # 10kswap
        ],
        "myswap_id": None,
    },
    "USDC_USDT": {
        "base_token": "USDC",
        "quote_token": "USDT",
        "addresses": [
            "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",  # jediswap
            "0x0601f72228f73704e827de5bcd8dadaad52c652bb1e42bf492d90bbe22df2cec",  # sithswap
            "0x041a708cf109737a50baa6cbeb9adf0bf8d97112dc6cc80c7a458cbad35328b0",  # 10kswap
        ],
        "myswap_id": 5,
    },
    "STRK_USDC": {
        "base_token": "STRK",
        "quote_token": "USDC",
        "addresses": [
            "0x05726725e9507c3586cc0516449e2c74d9b201ab2747752bb0251aaa263c9a26",  # jediswap
            "0x00900978e650c11605629fc3eda15447d57e884431894973e4928d8cb4c70c24",  # sithswap
            "0x066733193503019e4e9472f598ff32f15951a0ddb8fb5001f0beaa8bd1fb6840",  # 10kswap
        ],
        "myswap_id": None,
    },
    "STRK_USDT": {
        "base_token": "STRK",
        "quote_token": "USDT",
        "addresses": [
            "0x0784a8ec64af2b45694b94875fe6adbb57fadf9e196aa1aa1d144d163d0d8c51",  # 10kswap
        ],
        "myswap_id": None,
    },
    "DAI_STRK": {
        "base_token": "DAI",
        "quote_token": "STRK",
        "addresses": [
            "0x048ddb56ceb74777d081a9ce684aaa78e98c286e14fc1badb3a9938e710d6866",  # jediswap
        ],
        "myswap_id": None,
    },
}


class ProtocolIDs(Enum):
    """
    This class contains the protocol IDs that are used in the system.
    """

    # hashstack protocols
    HASHSTACK_V0: str = "Hashstack_v0"
    HASHSTACK_V1: str = "Hashstack_v1"
    HASHSTACK_V1_R: str = "Hashstack_v1_r"
    HASHSTACK_V1_D: str = "Hashstack_v1_d"
    # nostra protocols
    NOSTRA_ALPHA: str = "Nostra_alpha"
    NOSTRA_MAINNET: str = "Nostra_mainnet"
    # zkLend protocol
    ZKLEND: str = "zkLend"

    @classmethod
    def choices(cls) -> list[str]:
        """
        This method returns the values of the enum.
        :return: list of values
        """
        return [choice.value for choice in cls]

# FIXME Uncomment when DAI is added correct address
PAIRS: list[str] = [
    "ETH-USDC",
    "ETH-USDT",
    # "ETH-DAI",
    # "ETH-DAI V2",
    "WBTC-USDC",
    "WBTC-USDT",
    # "WBTC-DAI",
    # "WBTC-DAI V2",
    "STRK-USDC",
    "STRK-USDT",
    # "STRK-DAI",
    # "STRK-DAI V2",
]

UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES = {
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "WBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    # "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    # "DAI V2": "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad",
}
