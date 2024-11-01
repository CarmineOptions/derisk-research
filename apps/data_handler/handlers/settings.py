"""
This module defines configuration settings for token pools and trading pairs used in DeFi protocols
like JediSwap and MySwap. It includes settings for supported trading pairs, token details, and pool
addresses and identifiers for various token pairs across protocols.
"""
import dataclasses
from decimal import Decimal


@dataclasses.dataclass
class TokenSettings:
    """
    Configuration for a token, including symbol, decimal factor, and blockchain address.
    """
    symbol: str
    # Source: Starkscan, e.g.
    # https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7
    # for ETH.
    decimal_factor: Decimal
    address: str


@dataclasses.dataclass
class JediSwapPoolSettings:
    """
    Settings for a JediSwap pool, including symbol, address, 
    and token addresses.
    """
    symbol: str
    address: str
    token_1: str
    token_2: str


# TODO: Introduce other pairs.
PAIRS: list[str] = [
    "ETH-USDC",
    "ETH-USDT",
    "ETH-DAI",
    "wBTC-USDC",
    "wBTC-USDT",
    "wBTC-DAI",
    "STRK-USDC",
    "STRK-USDT",
    "STRK-DAI",
]
TOKEN_PAIRS: dict[str, tuple[str, ...]] = {
    "ETH": ("USDC", "USDT", "DAI"),
    "wBTC": ("USDC", "USDT", "DAI"),
    "STRK": ("USDC", "USDT", "DAI"),
}

HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "JediSwap: DAI/ETH Pool":
    TokenSettings(
        symbol="JediSwap: DAI/ETH Pool",
        decimal_factor=Decimal("1e18"),
        address="0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
    ),
    "JediSwap: DAI/USDC Pool":
    TokenSettings(
        symbol="JediSwap: DAI/USDC Pool",
        decimal_factor=Decimal("1e18"),
        address="0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
    ),
    "JediSwap: DAI/USDT Pool":
    TokenSettings(
        symbol="JediSwap: DAI/USDT Pool",
        decimal_factor=Decimal("1e18"),
        address="0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
    ),
    "JediSwap: ETH/USDC Pool":
    TokenSettings(
        symbol="JediSwap: ETH/USDC Pool",
        decimal_factor=Decimal("1e18"),
        address="0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    ),
    "JediSwap: ETH/USDT Pool":
    TokenSettings(
        symbol="JediSwap: ETH/USDT Pool",
        decimal_factor=Decimal("1e18"),
        address="0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
    ),
    "JediSwap: USDC/USDT Pool":
    TokenSettings(
        symbol="JediSwap: USDC/USDT Pool",
        decimal_factor=Decimal("1e18"),
        address="0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
    ),
    "JediSwap: WBTC/ETH Pool":
    TokenSettings(
        symbol="JediSwap: WBTC/ETH Pool",
        decimal_factor=Decimal("1e18"),
        address="0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
    ),
    "JediSwap: WBTC/USDC Pool":
    TokenSettings(
        symbol="JediSwap: WBTC/USDC Pool",
        decimal_factor=Decimal("1e18"),
        address="0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
    ),
    "JediSwap: WBTC/USDT Pool":
    TokenSettings(
        symbol="JediSwap: WBTC/USDT Pool",
        decimal_factor=Decimal("1e18"),
        address="0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
    ),
    "mySwap: DAI/ETH Pool":
    TokenSettings(
        symbol="mySwap: DAI/ETH Pool",
        decimal_factor=Decimal("1e18"),
        address="0x07c662b10f409d7a0a69c8da79b397fd91187ca5f6230ed30effef2dceddc5b3",
    ),
    "mySwap: DAI/USDC Pool":
    TokenSettings(
        symbol="mySwap: DAI/USDC Pool",
        decimal_factor=Decimal("1e12"),
        address="0x0611e8f4f3badf1737b9e8f0ca77dd2f6b46a1d33ce4eed951c6b18ac497d505",
    ),
    "mySwap: ETH/USDC Pool":
    TokenSettings(
        symbol="mySwap: ETH/USDC Pool",
        decimal_factor=Decimal("1e12"),
        address="0x022b05f9396d2c48183f6deaf138a57522bcc8b35b67dee919f76403d1783136",
    ),
    "mySwap: ETH/USDT Pool":
    TokenSettings(
        symbol="mySwap: ETH/USDT Pool",
        decimal_factor=Decimal("1e12"),
        address="0x041f9a1e9a4d924273f5a5c0c138d52d66d2e6a8bee17412c6b0f48fe059ae04",
    ),
    "mySwap: USDC/USDT Pool":
    TokenSettings(
        symbol="mySwap: USDC/USDT Pool",
        decimal_factor=Decimal("1e6"),
        address="0x01ea237607b7d9d2e9997aa373795929807552503683e35d8739f4dc46652de1",
    ),
    "mySwap: WBTC/USDC Pool":
    TokenSettings(
        symbol="mySwap: WBTC/USDC Pool",
        decimal_factor=Decimal("1e7"),
        address="0x025b392609604c75d62dde3d6ae98e124a31b49123b8366d7ce0066ccb94f696",
    ),
}

JEDISWAP_POOL_SETTINGS: dict[str, JediSwapPoolSettings] = {
    "JediSwap: DAI/ETH Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: DAI/ETH Pool",
        address="0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
        token_1="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        token_2="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "JediSwap: DAI/USDC Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: DAI/USDC Pool",
        address="0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
        token_1="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        token_2="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "JediSwap: DAI/USDT Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: DAI/USDT Pool",
        address="0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
        token_1="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        token_2="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "JediSwap: ETH/USDC Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: ETH/USDC Pool",
        address="0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
        token_1="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        token_2="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "JediSwap: ETH/USDT Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: ETH/USDT Pool",
        address="0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
        token_1="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        token_2="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "JediSwap: USDC/USDT Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: USDC/USDT Pool",
        address="0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
        token_1="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        token_2="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "JediSwap: WBTC/ETH Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: WBTC/ETH Pool",
        address="0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
        token_1="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        token_2="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "JediSwap: WBTC/USDC Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: WBTC/USDC Pool",
        address="0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
        token_1="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        token_2="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "JediSwap: WBTC/USDT Pool":
    JediSwapPoolSettings(
        symbol="JediSwap: WBTC/USDT Pool",
        address="0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
        token_1="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        token_2="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
}


@dataclasses.dataclass
class MySwapPoolSettings:
    """Settings for a MySwap pool: symbol, address, 
    ID, and token addresses."""
    symbol: str
    address: str
    myswap_id: int
    token_1: str
    token_2: str


MYSWAP_POOL_SETTINGS: dict[str, MySwapPoolSettings] = {
    "mySwap: DAI/ETH Pool":
    MySwapPoolSettings(
        symbol="mySwap: DAI/ETH Pool",
        address="0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
        myswap_id=2,
        token_1="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        token_2="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "mySwap: DAI/USDC Pool":
    MySwapPoolSettings(
        symbol="mySwap: DAI/USDC Pool",
        address="0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
        myswap_id=6,
        token_1="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
        token_2="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "mySwap: ETH/USDC Pool":
    MySwapPoolSettings(
        symbol="mySwap: ETH/USDC Pool",
        address="0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
        myswap_id=1,
        token_1="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        token_2="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "mySwap: ETH/USDT Pool":
    MySwapPoolSettings(
        symbol="mySwap: ETH/USDT Pool",
        address="0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
        myswap_id=4,
        token_1="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
        token_2="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "mySwap: USDC/USDT Pool":
    MySwapPoolSettings(
        symbol="mySwap: USDC/USDT Pool",
        address="0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
        myswap_id=5,
        token_1="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
        token_2="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "mySwap: WBTC/USDC Pool":
    MySwapPoolSettings(
        symbol="mySwap: WBTC/USDC Pool",
        address="0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
        myswap_id=3,
        token_1="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
        token_2="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
}
