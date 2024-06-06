from dataclasses import dataclass


@dataclass
class TokenConfig:
    name: str
    decimals: int


TOKEN_MAPPING = {
    "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7": TokenConfig(
        name="ETH", decimals=18
    ),
    "0x53c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8": TokenConfig(
        name="USDC", decimals=6
    ),
    "0x05fa6cc6185eab4b0264a4134e2d4e74be11205351c7c91196cb27d5d97f8d21": TokenConfig(
        name="USDT", decimals=6
    ),
    "0x019c981ec23aa9cbac1cc1eb7f92cf09ea2816db9cbd932e251c86a2e8fb725f": TokenConfig(
        name="DAI", decimals=18
    ),
    "0x01320a9910e78afc18be65e4080b51ecc0ee5c0a8b6cc7ef4e685e02b50e57ef": TokenConfig(
        name="wBTC", decimals=8
    ),
    "0x07514ee6fa12f300ce293c60d60ecce0704314defdb137301dae78a7e5abbdd7": TokenConfig(
        name="STRK", decimals=18
    ),
    "0x0719b5092403233201aa822ce928bd4b551d0cdb071a724edd7dc5e5f57b7f34": TokenConfig(
        name="UNO", decimals=18
    ),
    "0x00585c32b625999e6e5e78645ff8df7a9001cf5cf3eb6b80ccdd16cb64bd3a34": TokenConfig(
        name="ZEND", decimals=18
    ),
    "0x07e2c010c0b381f347926d5a203da0335ef17aefee75a89292ef2b0f94924864": TokenConfig(
        name="wstETH", decimals=18
    ),
    "0x4c4fb1ab068f6039d5780c68dd0fa2f8742cceb3426d19667778ca7f3518a9": TokenConfig(
        name="LORDS", decimals=18
    ),
}