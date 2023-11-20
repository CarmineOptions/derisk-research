# TODO: rename to settings.py?
import dataclasses
import decimal



@dataclasses.dataclass
class TokenSettings:
    symbol: str
    # Source: Starkscan, e.g. 
    # https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
    decimal_factor: decimal.Decimal
    address: str


TOKEN_SETTINGS: dict[str, TokenSettings] = {
    "ETH": TokenSettings(
        symbol="ETH",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    ),
    "wBTC": TokenSettings(
        symbol="wBTC",
        decimal_factor=decimal.Decimal("1e8"),
        address="0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    ),
    "USDC": TokenSettings(
        symbol="USDC",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    ),
    "DAI": TokenSettings(
        symbol="DAI",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    ),
    "USDT": TokenSettings(
        symbol="USDT",
        decimal_factor=decimal.Decimal("1e6"),
        address="0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    ),
    "wstETH": TokenSettings(
        symbol="wstETH",
        decimal_factor=decimal.Decimal("1e18"),
        address="0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",
    ),
}


# TODO: Introduce other pairs.
PAIRS: list[str] = [
    "ETH-USDC",
    "ETH-USDT",
    "ETH-DAI",
    "wBTC-USDC",
    "wBTC-USDT",
    "wBTC-DAI",
]


# TODO: Improve this.
def get_symbol(address):
    # you can match addresses as numbers
    n = int(address, base=16)
    symbol_address_map = {token: token_settings.address for token, token_settings in TOKEN_SETTINGS.items()}
    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol
    raise KeyError(f"Address = {address} does not exist in the symbol table.")


def ztoken_to_token(symbol):
    if symbol == "zWBTC":
        # weird exception
        return "wBTC"
    if symbol.startswith("z"):
        return symbol[1:]
    else:
        return symbol
