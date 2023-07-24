from decimal import Decimal
import time

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
            time.sleep(5)
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
