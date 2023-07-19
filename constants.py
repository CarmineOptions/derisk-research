from enum import Enum


class Protocol(Enum):
    HASHSTACK = "0x03dcf5c72ba60eb7b2fe151032769d49dd3df6b04fa3141dffd6e2aa162b7a6e"
    ZKLEND = "0x04c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05"


class Table(Enum):
    EVENTS = "starkscan_events"
    BLOCKS = "blocks"
    PRICES = "oracle_prices"


symbol_address_map = {
    "ETH": "0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",
    "wBTC": "0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",
    "USDC": "0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8",
    "DAI": "0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",
    "USDT": "0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",
}

symbol_decimals_map = {
    "ETH": 18,
    "wBTC": 8,
    "USDC": 6,
    "DAI": 18,
    "USDT": 6,
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
    return symbol[1:] if symbol.startswith("z") else symbol
