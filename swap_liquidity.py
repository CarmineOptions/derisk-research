from blockchain_call import balance_of
from constants import get_address, get_decimals


class Token:
    def __init__(self, symbol) -> None:
        self.symbol = symbol
        self.address = get_address(self.symbol)
        self.decimals = get_decimals(self.symbol)


class Pair:
    def tokens_to_id(self, t1, t2):
        (first, second) = tuple(sorted((t1, t2)))
        return f"{first}/{second}"


class Pool(Pair):
    def __init__(self, t1, t2, address):
        self.id = self.tokens_to_id(t1, t2)
        self.address = address
        self.tokens = [Token(t1), Token(t2)]


class SwapAmm(Pair):
    def __init__(self, name):
        self.name = name
        self.pools = {}

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
                    t = cur_token
                    balance += await balance_of(cur_token.address, pool.address)
        return (t, balance)
