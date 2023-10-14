import decimal
import enum


# TODO: Introduce other pairs.
PAIRS = [
    "ETH-USDC",
    "ETH-USDT",
    "ETH-DAI",
    "wBTC-USDC",
    "wBTC-USDT",
    "wBTC-DAI",
    # "ETH-wBTC",
    # "wBTC-ETH",
]


# Source: Starkscan, e.g.
# https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
TOKEN_DECIMAL_FACTORS = {
    "ETH": decimal.Decimal("1e18"),
    "wBTC": decimal.Decimal("1e8"),
    "USDC": decimal.Decimal("1e6"),
    "DAI": decimal.Decimal("1e18"),
    "USDT": decimal.Decimal("1e6"),
}


# Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
COLLATERAL_FACTORS = {
    "ETH": decimal.Decimal("0.80"),
    "wBTC": decimal.Decimal("0.70"),
    "USDC": decimal.Decimal("0.80"),
    "DAI": decimal.Decimal("0.70"),
    "USDT": decimal.Decimal("0.70"),
}


# Source: https://zklend.gitbook.io/documentation/using-zklend/technical/asset-parameters.
LIQUIDATION_BONUSES = {
    "ETH": decimal.Decimal("0.10"),
    "wBTC": decimal.Decimal("0.15"),
    "USDC": decimal.Decimal("0.10"),
    "DAI": decimal.Decimal("0.10"),
    "USDT": decimal.Decimal("0.10"),
}


class Protocol(enum.Enum):
    HASHSTACK = "0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e"
    ZKLEND = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"


class Table(enum.Enum):
    EVENTS = "starkscan_events"
    BLOCKS = "blocks"
    PRICES = "oracle_prices"


symbol_address_map = {
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "wBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
    "zETH": "0x01b5bd713e72fdc5d63ffd83762f81297f6175a5e0a4771cdadbc1dd5fe72cb1",
    "zUSDC": "0x047ad51726d891f972e74e4ad858a261b43869f7126ce7436ee0b2529a98f486",
    "zUSDT": "0x00811d8da5dc8a2206ea7fd0b28627c2d77280a515126e62baa4d78e22714c4a",
    "zDAI": "0x062fa7afe1ca2992f8d8015385a279f49fad36299754fb1e9866f4f052289376",
    "zWBTC": "0x02b9ea3acdb23da566cee8e8beae3125a1458e720dea68c4a9a7a2d8eb5bbb4a",
}

symbol_decimals_map = {
    "ETH": 18,
    "wBTC": 8,
    "USDC": 6,
    "DAI": 18,
    "USDT": 6,
    "zETH": 18,
    "zUSDC": 6,
    "zUSDT": 6,
    "zDAI": 18,
    "zWBTC": 8,
}


def get_address(symbol):
    try:
        return symbol_address_map[symbol]
    except KeyError:
        raise KeyError(f"Symbol '{symbol}' does not exist in the symbol table.")


def get_symbol(address):
    # you can match addresses as numbers
    n = int(address, base=16)
    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol
    raise KeyError(f"Address '{address}' does not exist in the symbol table.")


def get_decimals(symbol):
    if symbol in symbol_decimals_map:
        return symbol_decimals_map[symbol]
    else:
        raise KeyError(f"Symbol '{symbol}' does not exist in the decimals map")


def ztoken_to_token(symbol):
    if symbol == "zWBTC":
        # weird exception
        return "wBTC"
    if symbol.startswith("z"):
        return symbol[1:]
    else:
        return symbol
