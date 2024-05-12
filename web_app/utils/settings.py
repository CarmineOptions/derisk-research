from dataclasses import dataclass
from decimal import Decimal


@dataclass
class TokenSettings:
    symbol: str
    decimal_factor: Decimal
    address: str


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
    "DAI": TokenSettings(
        symbol="DAI",
        decimal_factor=Decimal("1e18"),
        address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    ),
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
