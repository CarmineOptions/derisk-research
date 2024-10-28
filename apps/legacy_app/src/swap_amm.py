import asyncio
import dataclasses
import decimal
from typing import Optional, Union

import requests

import src.blockchain_call
import src.hashstack_v1

# import src.helpers
import src.settings

AMMS = ["10kSwap", "MySwap", "SithSwap", "JediSwap"]


# # TODO
# import src.types  # TODO
# class Prices:

#     def __init__(self):
#         # TODO: Move this mapping to `src.settings.TOKEN_SETTINGS`.
#         self.tokens = [
#             ("ethereum", "ETH"),
#             ("bitcoin", "WBTC"),
#             ("usd-coin", "USDC"),
#             ("dai", "DAI"),
#             ("tether", "USDT"),
#             ("wrapped-steth", "wstETH"),
#             ("lords", "LORDS"),
#             ("starknet", "STRK"),
#        ]
#         self.vs_currency = "usd"
#         self.prices: src.types.Prices = src.types.Prices()
#         self.get_prices()

#     def get_prices(self):
#         token_ids = ""
#         for token in self.tokens:
#             token_ids += f"{token[0]},"
#         url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_ids}&vs_currencies={self.vs_currency}"
#         response = requests.get(url)
#         if response.status_code == 200:
#             data = response.json()
#             for token in self.tokens:
#                 (id, symbol) = token
#                 self.prices[symbol] = decimal.Decimal(data[id][self.vs_currency])
#         else:
#             raise Exception(f"Failed getting prices, status code = {response.status_code}.")

#     async def get_lp_token_prices(self) -> None:
#         lp_token_pools = LPTokenPools()
#         await lp_token_pools.get_data()
#         for lp_token, lp_token_pool in lp_token_pools.pools.items():
#             self.prices[lp_token] = _get_lp_token_price(pool=lp_token_pool, prices=self.prices)


@dataclasses.dataclass
class SwapAmmToken(src.settings.TokenSettings):
    # TODO: Improve this.
    balance_base: Optional[float] = 0
    balance_converted: Optional[float] = 0


class Pair:
    def tokens_to_id(self, undelying_symbol_a: str, underlying_symbol_b: str):
        (first, second) = tuple(sorted((undelying_symbol_a, underlying_symbol_b)))
        return f"{first}/{second}"


class Pool(Pair):
    def __init__(
        self,
        underlying_symbol_a: str,
        underlying_symbol_b: str,
        pool_addresses: dict[str, str],
        myswap_id: int,
    ):
        self.underlying_symbol_a: str = underlying_symbol_a
        self.underlying_symbol_b: str = underlying_symbol_b
        self.pool_addresses: dict[str, str] = pool_addresses
        self.myswap_id: int = myswap_id

        self.id: str = self.tokens_to_id(
            undelying_symbol_a=underlying_symbol_a,
            underlying_symbol_b=underlying_symbol_b,
        )
        self.balances: dict[str, dict[str, float]] = {
            amm: {
                underlying_symbol_a: 0.0,
                underlying_symbol_b: 0.0,
            }
            for amm in pool_addresses.keys()
        }
        t1 = SwapAmmToken(
            symbol=src.settings.TOKEN_SETTINGS[underlying_symbol_a].symbol,
            decimal_factor=src.settings.TOKEN_SETTINGS[
                underlying_symbol_a
            ].decimal_factor,
            address=src.settings.TOKEN_SETTINGS[underlying_symbol_a].address,
        )
        t2 = SwapAmmToken(
            symbol=src.settings.TOKEN_SETTINGS[underlying_symbol_b].symbol,
            decimal_factor=src.settings.TOKEN_SETTINGS[
                underlying_symbol_b
            ].decimal_factor,
            address=src.settings.TOKEN_SETTINGS[underlying_symbol_b].address,
        )
        self.tokens = [t1, t2]

    async def get_balance(self):
        if self.myswap_id is not None:
            myswap_pool = await src.blockchain_call.get_myswap_pool(self.myswap_id)
        for token in self.tokens:
            balance = 0.0
            for amm, address in self.pool_addresses.items():
                amm_balance = 0.0
                balance += await src.blockchain_call.balance_of(token.address, address)
                amm_balance = balance
                self.balances[amm][token.symbol] += amm_balance / token.decimal_factor
            if self.myswap_id is not None:
                balance += myswap_pool[token.symbol.upper()]
            token.balance_base = balance
            token.balance_converted = balance / token.decimal_factor

    def update_converted_balance(self):
        for token in self.tokens:
            token.balance_converted = token.balance_base

    def buy_tokens(self, symbol: str, amount: float):
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

        const = buy.balance_base * sell.balance_base
        new_buy = buy.balance_base - amount
        new_sell = const / new_buy
        tokens_paid = new_sell - sell.balance_base

        buy.balance_base = new_buy
        sell.balance_base = new_sell
        self.update_converted_balance()

        return tokens_paid

    def supply_at_price(self, initial_price: float, amm: str = None):
        if amm is None:
            constant = (
                self.tokens[0].balance_converted * self.tokens[1].balance_converted
            )
        elif not amm in self.balances.keys():
            return 0
        else:
            constant = (
                self.balances[amm][self.tokens[0].symbol]
                * self.balances[amm][self.tokens[1].symbol]
            )
        # TODO: Use just floats, no point in using decimals.
        return ((initial_price * float(constant)) ** 0.5) * (1.0 - 0.95**0.5)


class SwapAmm(Pair):
    # TODO: Fix this to reflect that there's 2 DAI tokens now:
    #  'DAI': '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3'
    #  'DAI V2': '0x05574eb6b8789a91466f902c380d978e472db68170ff82a5b650b95a58ddf4ad'

    async def init(self):
        # TODO: Add AVNU
        self.pools = {}
        self.add_pool(
            "ETH",
            "USDC",
            {
                "JediSwap": "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",
                "SithSwap": "0x030615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f",
                "10kSwap": "0x000023c72abdf49dffc85ae3ede714f2168ad384cc67d08524732acea90df325",
                "MySwap": "0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",
            },
            1,
        )
        self.add_pool(
            "DAI",
            "ETH",
            {
                "JediSwap": "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",
                "SithSwap": "0x0032ebb8e68553620b97b308684babf606d9556d5c0a652450c32e85f40d000d",
                "10kSwap": "0x017e9e62c04b50800d7c59454754fe31a2193c9c3c6c92c093f2ab0faadf8c87",
            },
            2,
        )
        self.add_pool(
            "ETH",
            "USDT",
            {
                "JediSwap": "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",
                "SithSwap": "0x00691fa7f66d63dc8c89ff4e77732fff5133f282e7dbd41813273692cc595516",
                "10kSwap": "0x05900cfa2b50d53b097cb305d54e249e31f24f881885aae5639b0cd6af4ed298",
            },
            4,
        )
        self.add_pool(
            "WBTC",
            "ETH",
            {
                "JediSwap": "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",
                "10kSwap": "0x02a6e0ecda844736c4803a385fb1372eff458c365d2325c7d4e08032c7a908f3",
            },
        )
        self.add_pool(
            "WBTC",
            "USDC",
            {
                "JediSwap": "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",
                "10kSwap": "0x022e45d94d5c6c477d9efd440aad71b2c02a5cd5bed9a4d6da10bb7c19fd93ba",
            },
            3,
        )
        self.add_pool(
            "WBTC",
            "USDT",
            {
                "JediSwap": "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",
                "10kSwap": "0x050031010bcee2f43575b3afe197878e064e1a03c12f2ff437f29a2710e0b6ef",
            },
        )
        self.add_pool(
            "DAI",
            "WBTC",
            {
                "JediSwap": "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",
                "10kSwap": "0x00f9d8f827734f5fd54571f0e78398033a3c1f1074a471cd4623f2aa45163718",
            },
        )
        self.add_pool(
            "DAI",
            "USDC",
            {
                "JediSwap": "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",
                "SithSwap": "0x015e9cd2d4d6b4bb9f1124688b1e6bc19b4ff877a01011d28c25c9ee918e83e5",
                "10kSwap": "0x02e767b996c8d4594c73317bb102c2018b9036aee8eed08ace5f45b3568b94e5",
            },
            6,
        )
        self.add_pool(
            "DAI",
            "USDT",
            {
                "JediSwap": "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",
                "10kSwap": "0x041d52e15e82b003bf0ad52ca58393c87abef3e00f1bf69682fd4162d5773f8f",
            },
        )
        self.add_pool(
            "USDC",
            "USDT",
            {
                "JediSwap": "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",
                "SithSwap": "0x0601f72228f73704e827de5bcd8dadaad52c652bb1e42bf492d90bbe22df2cec",
                "10kSwap": "0x041a708cf109737a50baa6cbeb9adf0bf8d97112dc6cc80c7a458cbad35328b0",
            },
            5,
        )
        self.add_pool(
            "STRK",
            "USDC",
            {
                "JediSwap": "0x05726725e9507c3586cc0516449e2c74d9b201ab2747752bb0251aaa263c9a26",
                "SithSwap": "0x00900978e650c11605629fc3eda15447d57e884431894973e4928d8cb4c70c24",
                "10kSwap": "0x066733193503019e4e9472f598ff32f15951a0ddb8fb5001f0beaa8bd1fb6840",
            },
            None,
        )
        self.add_pool(
            "STRK",
            "USDT",
            {
                "10kSwap": "0x0784a8ec64af2b45694b94875fe6adbb57fadf9e196aa1aa1d144d163d0d8c51"
            },
            None,
        )
        self.add_pool(
            "DAI",
            "STRK",
            {
                "JediSwap": "0x048ddb56ceb74777d081a9ce684aaa78e98c286e14fc1badb3a9938e710d6866"
            },
            None,
        )
        await self.get_balance()

    async def get_balance(self):
        for pool in self.pools.values():
            await pool.get_balance()

    def add_pool(
        self,
        t1: str,
        t2: str,
        pool_addresses: dict[str, str],
        myswap_id: int | None = None,
    ):
        pool = Pool(
            t1,
            t2,
            pool_addresses,
            myswap_id,
        )
        self.pools[pool.id] = pool

    def get_pool(self, token_a: str, token_b: str):
        # TODO: Rename DAI V2 to DAI until we can handle both.
        token_a = token_a.replace("DAI V2", "DAI")
        token_b = token_b.replace("DAI V2", "DAI")
        try:
            return self.pools[self.tokens_to_id(token_a, token_b)]
        except:
            raise Exception(
                f"Trying to get pool that is not set: {self.tokens_to_id(token_a, token_b)}"
            )

    def get_supply_at_price(
        self,
        collateral_token_underlying_symbol: str,
        collateral_token_price: float,
        debt_token_underlying_symbol: str,
        amm: str,
    ):
        pool: Pool = self.get_pool(
            token_a=collateral_token_underlying_symbol,
            token_b=debt_token_underlying_symbol,
        )
        return pool.supply_at_price(
            initial_price=collateral_token_price,
            amm=amm,
        )
