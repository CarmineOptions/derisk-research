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

    def total_balance(self, token):
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


async def get_sithswap():
    # Setup the AMM.
    sithswap = SwapAmm("SithSwap")
    sithswap.add_pool(
        "ETH",
        "USDC",
        "0x030615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f",
    )
    sithswap.add_pool(
        "DAI",
        "ETH",
        "0x0032ebb8e68553620b97b308684babf606d9556d5c0a652450c32e85f40d000d",
    )
    sithswap.add_pool(
        "ETH",
        "USDT",
        "0x00691fa7f66d63dc8c89ff4e77732fff5133f282e7dbd41813273692cc595516",
    )
    sithswap.add_pool(
        "USDC",
        "USDT",
        "0x0601f72228f73704e827de5bcd8dadaad52c652bb1e42bf492d90bbe22df2cec",
    )
    sithswap.add_pool(
        "DAI",
        "USDC",
        "0x015e9cd2d4d6b4bb9f1124688b1e6bc19b4ff877a01011d28c25c9ee918e83e5",
    )
    await sithswap.get_balance()
    return sithswap


async def get_tenkswap():
    # Setup the AMM.
    tenkswap = SwapAmm("10KSwap")
    tenkswap.add_pool(
        "ETH",
        "USDC",
        "0x000023c72abdf49dffc85ae3ede714f2168ad384cc67d08524732acea90df325",
    )
    tenkswap.add_pool(
        "ETH",
        "USDT",
        "0x05900cfa2b50d53b097cb305d54e249e31f24f881885aae5639b0cd6af4ed298",
    )
    tenkswap.add_pool(
        "DAI",
        "ETH",
        "0x017e9e62c04b50800d7c59454754fe31a2193c9c3c6c92c093f2ab0faadf8c87",
    )
    tenkswap.add_pool(
        "wBTC",
        "USDC",
        "0x022e45d94d5c6c477d9efd440aad71b2c02a5cd5bed9a4d6da10bb7c19fd93ba",
    )
    tenkswap.add_pool(
        "DAI",
        "wBTC",
        "0x00f9d8f827734f5fd54571f0e78398033a3c1f1074a471cd4623f2aa45163718",
    )
    tenkswap.add_pool(
        "DAI",
        "USDC",
        "0x02e767b996c8d4594c73317bb102c2018b9036aee8eed08ace5f45b3568b94e5",
    )
    tenkswap.add_pool(
        "wBTC",
        "USDT",
        "0x050031010bcee2f43575b3afe197878e064e1a03c12f2ff437f29a2710e0b6ef",
    )
    tenkswap.add_pool(
        "USDC",
        "USDT",
        "0x041a708cf109737a50baa6cbeb9adf0bf8d97112dc6cc80c7a458cbad35328b0",
    )
    tenkswap.add_pool(
        "DAI",
        "USDT",
        "0x041d52e15e82b003bf0ad52ca58393c87abef3e00f1bf69682fd4162d5773f8f",
    )
    tenkswap.add_pool(
        "wBTC",
        "ETH",
        "0x02a6e0ecda844736c4803a385fb1372eff458c365d2325c7d4e08032c7a908f3",
    )
    await tenkswap.get_balance()
    return tenkswap


async def get_myswap():
    # Setup the AMM.
    myswap = SwapAmm("MySwap")
    myswap.add_pool(
        "ETH",
        "USDC",
        "0x022b05f9396d2c48183f6deaf138a57522bcc8b35b67dee919f76403d1783136",
    )
    myswap.add_pool(
        "DAI",
        "ETH",
        "0x07c662b10f409d7a0a69c8da79b397fd91187ca5f6230ed30effef2dceddc5b3",
    )
    myswap.add_pool(
        "USDC",
        "USDT",
        "0x01ea237607b7d9d2e9997aa373795929807552503683e35d8739f4dc46652de1",
    )
    myswap.add_pool(
        "ETH",
        "USDT",
        "0x041f9a1e9a4d924273f5a5c0c138d52d66d2e6a8bee17412c6b0f48fe059ae04",
    )
    myswap.add_pool(
        "wBTC",
        "USDC",
        "0x025b392609604c75d62dde3d6ae98e124a31b49123b8366d7ce0066ccb94f696",
    )
    myswap.add_pool(
        "DAI",
        "USDC",
        "0x0611e8f4f3badf1737b9e8f0ca77dd2f6b46a1d33ce4eed951c6b18ac497d505",
    )
    await myswap.get_balance()
    return myswap
