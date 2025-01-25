"""
A module for setting up tokens.
"""

from dataclasses import dataclass


@dataclass
class TokenSettings:
    """
    This class represents the structure and properties of a token it has a
    symbol, address and decimal factor.
    """

    symbol: str
    # Source: Starkscan, e.g.
    # https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7
    # for ETH.
    decimal_factor: float
    address: str


# TODO: remove after we get the params otherwise
# TODO: add ZEND, UNO, etc.
TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "ETH": TokenSettings(
        symbol="ETH",
        decimal_factor=1e18,
        address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "WBTC": TokenSettings(
        symbol="WBTC",
        decimal_factor=1e8,
        address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    ),
    "USDC": TokenSettings(
        symbol="USDC",
        decimal_factor=1e6,
        address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "DAI": TokenSettings(
        symbol="DAI",
        decimal_factor=1e18,
        address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    ),
    "USDT": TokenSettings(
        symbol="USDT",
        decimal_factor=1e6,
        address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "wstETH": TokenSettings(
        symbol="wstETH",
        decimal_factor=1e18,
        address="0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",
    ),
    "LORDS": TokenSettings(
        symbol="LORDS",
        decimal_factor=1e18,
        address="0x0124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",
    ),
    "STRK": TokenSettings(
        symbol="STRK",
        decimal_factor=1e18,
        address="0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    ),
}


# TODO: Introduce other pairs.
# TODO: Define the addresses first, then map
# TODO:(static or dynamic (with special treatment of DAI)?) to symbols.
PAIRS: list[str] = [
    "ETH-USDC",
    "ETH-USDT",
    "ETH-DAI",
    "ETH-DAI V2",
    "WBTC-USDC",
    "WBTC-USDT",
    "WBTC-DAI",
    "WBTC-DAI V2",
    "STRK-USDC",
    "STRK-USDT",
    "STRK-DAI",
    "STRK-DAI V2",
]

COLLATERAL_TOKENS = ["ETH", "WBTC", "STRK"]

STABLECOIN_BUNDLE_NAME = "(All USD Stable Coins)"

DEBT_TOKENS = ["USDC", "USDT", "DAI", "DAI V2", STABLECOIN_BUNDLE_NAME]

UNDERLYING_SYMBOLS_TO_UNDERLYING_ADDRESSES = {
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "WBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    "STRK": "0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d",
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    "DAI V2": "0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad",
}
