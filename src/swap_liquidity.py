from decimal import Decimal

from src.blockchain_call import balance_of
from src.constants import get_address, get_decimals


class Token:
    def __init__(self, symbol) -> None:
        self.symbol = symbol
        self.address = get_address(self.symbol)
        self.decimals = get_decimals(self.symbol)
        self.balance_base = None
        self.balance_converted = None


class Pair:
    def tokens_to_id(self, t1, t2):
        (first, second) = tuple(sorted((t1, t2)))
        return f"{first}/{second}"


class Pool(Pair):
    def __init__(self, symbol1, symbol2, address):
        self.id = self.tokens_to_id(symbol1, symbol2)
        self.address = address
        t1 = Token(symbol1)
        t2 = Token(symbol2)
        setattr(self, symbol1, t1)
        setattr(self, symbol2, t2)
        self.tokens = [t1, t2]

    async def get_balance(self):
        for token in self.tokens:
            balance = await balance_of(token.address, self.address)
            token.balance_base = balance
            token.balance_converted = Decimal(
                balance) / Decimal(10**token.decimals)

    def update_converted_balance(self):
        for token in self.tokens:
            token.balance_converted = Decimal(token.balance_base) / Decimal(
                10**token.decimals
            )

    def buy_tokens(self, symbol, amount):
        # assuming constant product function
        buy = None
        sell = None
        if self.tokens[0].symbol == symbol:
            buy = self.tokens[0]
            sell = self.tokens[1]
        elif self.tokens[1].symbol == symbol:
            buy = self.tokens[1]
            sell = self.tokens[0]
        else:
            raise Exception(f"Could not buy {symbol}")
        const = Decimal(buy.balance_base) * Decimal(sell.balance_base)
        new_buy = buy.balance_base - amount
        new_sell = const / Decimal(new_buy)
        tokens_paid = round(new_sell - sell.balance_base)
        buy.balance_base = new_buy
        sell.balance_base = new_sell
        self.update_converted_balance()
        return tokens_paid

    def supply_at_price(self, symbol: str, initial_price: Decimal):
        # assuming constant product function
        constant = (
            Decimal(self.tokens[0].balance_base)
            / (Decimal("10") ** Decimal(f"{self.tokens[0].decimals}"))
        ) * (
            Decimal(self.tokens[1].balance_base)
            / (Decimal("10") ** Decimal(f"{self.tokens[1].decimals}"))
        )
        return (initial_price * constant) ** Decimal("0.5") * (
            Decimal("1") - Decimal("0.95") ** Decimal("0.5")
        )


class SwapAmm(Pair):
    def __init__(self, name):
        self.name = name
        self.pools = {}

    async def get_balance(self):
        for pool in self.pools.values():
            await pool.get_balance()

    def add_pool(self, t1, t2, address):
        pool = Pool(t1, t2, address)
        self.pools[pool.id] = pool

    def get_pool(self, t1, t2):
        try:
            return self.pools[self.tokens_to_id(t1, t2)]
        except:
            raise Exception(
                f"Trying to get pool that is not set: {self.tokens_to_id(t1, t2)}"
            )

    async def total_balance(self, token):
        balance = 0
        t = None
        for pool in self.pools.values():
            for cur_token in pool.tokens:
                if cur_token.symbol == token:
                    balance += token.balance_base
        return balance


async def get_jediswap():
    # Setup the AMM.
    jediswap = SwapAmm("JediSwap")
    jediswap.add_pool(
        "ETH",
        "USDC",
        "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
    )
    jediswap.add_pool(
        "DAI",
        "ETH",
        "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
    )
    jediswap.add_pool(
        "ETH",
        "USDT",
        "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
    )
    jediswap.add_pool(
        "wBTC",
        "ETH",
        "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
    )
    jediswap.add_pool(
        "wBTC",
        "USDC",
        "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
    )
    jediswap.add_pool(
        "wBTC",
        "USDT",
        "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
    )
    jediswap.add_pool(
        "DAI",
        "wBTC",
        "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",
    )
    jediswap.add_pool(
        "DAI",
        "USDC",
        "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
    )
    jediswap.add_pool(
        "DAI",
        "USDT",
        "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
    )
    jediswap.add_pool(
        "USDC",
        "USDT",
        "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
    )
    await jediswap.get_balance()
    return jediswap
