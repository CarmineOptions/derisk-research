""" Constants for order books """
from dataclasses import dataclass


@dataclass
class TokenConfig:
    """tokenconfig class docstring"""
    name: str
    decimals: int


TOKEN_MAPPING = {
    "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7":
    TokenConfig(name="ETH", decimals=18),
    "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8":
    TokenConfig(name="USDC", decimals=6),
    "0x68f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8":
    TokenConfig(name="USDT", decimals=6),
    "0x0da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3":
    TokenConfig(name="DAI", decimals=18),
    "0x3fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac":
    TokenConfig(name="wBTC", decimals=8),
    "0x4718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d":
    TokenConfig(name="STRK", decimals=18),
    "0x719b5092403233201aa822ce928bd4b551d0cdb071a724edd7dc5e5f57b7f34":
    TokenConfig(name="UNO", decimals=18),
    "0x0585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34":
    TokenConfig(name="ZEND", decimals=18),
    "0x42b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2":
    TokenConfig(name="wstETH", decimals=18),
    "0x124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49":
    TokenConfig(name="LORDS", decimals=18),
}
