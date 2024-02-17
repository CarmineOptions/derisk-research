from typing import Optional, Union
import dataclasses
import decimal
import requests

import src.blockchain_call
import src.hashstack_v1
import src.helpers
import src.settings



@dataclasses.dataclass
class JediSwapPoolSettings():
    symbol: str
    address: str
    token_1: str
    token_2: str


JEDISWAP_POOL_SETTINGS: dict[str, JediSwapPoolSettings] = {
    'JediSwap: DAI/ETH Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: DAI/ETH Pool',
        address = '0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138',
        token_1 = '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',
        token_2 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
    ),
    'JediSwap: DAI/USDC Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: DAI/USDC Pool',
        address = '0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b',
        token_1 = '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',
        token_2 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
    ),
    'JediSwap: DAI/USDT Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: DAI/USDT Pool',
        address = '0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767',
        token_1 = '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',
        token_2 = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
    ),
    'JediSwap: ETH/USDC Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: ETH/USDC Pool',
        address = '0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a',
        token_1 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
        token_2 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
    ),
    'JediSwap: ETH/USDT Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: ETH/USDT Pool',
        address = '0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6',
        token_1 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
        token_2 = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
    ),
    'JediSwap: USDC/USDT Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: USDC/USDT Pool',
        address = '0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b',
        token_1 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
        token_2 = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
    ),
    'JediSwap: WBTC/ETH Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: WBTC/ETH Pool',
        address = '0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c',
        token_1 = '0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac',
        token_2 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
    ),
    'JediSwap: WBTC/USDC Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: WBTC/USDC Pool',
        address = '0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8',
        token_1 = '0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac',
        token_2 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
    ),
    'JediSwap: WBTC/USDT Pool': JediSwapPoolSettings(
        symbol = 'JediSwap: WBTC/USDT Pool',
        address = '0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0',
        token_1 = '0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac',
        token_2 = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
    ),
}


@dataclasses.dataclass
class MySwapPoolSettings():
    symbol: str
    address: str
    myswap_id: int
    token_1: str
    token_2: str


MYSWAP_POOL_SETTINGS: dict[str, MySwapPoolSettings] = {
    'mySwap: DAI/ETH Pool': MySwapPoolSettings(
        symbol = 'mySwap: DAI/ETH Pool',
        address = '0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28',
        myswap_id = 2,
        token_1 = '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',
        token_2 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
    ),
    'mySwap: DAI/USDC Pool': MySwapPoolSettings(
        symbol = 'mySwap: DAI/USDC Pool',
        address = '0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28',
        myswap_id = 6,
        token_1 = '0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3',
        token_2 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
    ),
    'mySwap: ETH/USDC Pool': MySwapPoolSettings(
        symbol = 'mySwap: ETH/USDC Pool',
        address = '0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28',
        myswap_id = 1,
        token_1 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
        token_2 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
    ),
    'mySwap: ETH/USDT Pool': MySwapPoolSettings(
        symbol = 'mySwap: ETH/USDT Pool',
        address = '0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28',
        myswap_id = 4,
        token_1 = '0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7',
        token_2 = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
    ),
    'mySwap: USDC/USDT Pool': MySwapPoolSettings(
        symbol = 'mySwap: USDC/USDT Pool',
        address = '0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28',
        myswap_id = 5,
        token_1 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
        token_2 = '0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8',
    ),
    'mySwap: WBTC/USDC Pool': MySwapPoolSettings(
        symbol = 'mySwap: WBTC/USDC Pool',
        address = '0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28',
        myswap_id = 3,
        token_1 = '0x03fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac',
        token_2 = '0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8',
    ),
}



class JediSwapPool:
    """
    This class implements JediSwap pools where Hashstack V1 users can spend their debt. To properly account for their 
    token holdings, we collect the total supply of LP tokens and the amounts of both tokens in the pool.
    """

    def __init__(self, settings: JediSwapPoolSettings) -> None:
        self.settings: JediSwapPoolSettings = settings

        self.total_lp_supply: Optional[decimal.Decimal] = None
        self.token_amounts: Optional[src.helpers.TokenValues] = None

    async def get_data(self) -> None:
        self.total_lp_supply = decimal.Decimal(
            (
                await src.blockchain_call.func_call(
                    addr=self.settings.address, 
                    selector='totalSupply', 
                    calldata=[],
                )
            )[0]
        )
        self.token_amounts = src.helpers.TokenValues()
        for token in [self.settings.token_1, self.settings.token_2]:
            self.token_amounts.values[src.helpers.get_symbol(token)] = decimal.Decimal(
                await src.blockchain_call.balance_of(
                    token_addr=token, 
                    holder_addr=self.settings.address,
                )
            )


class MySwapPool:
    """
    This class implements MySwap pools where Hashstack V1 users can spend their debt. To properly account for their 
    token holdings, we collect the total supply of LP tokens and the amounts of both tokens in the pool.
    """

    def __init__(self, settings:MySwapPoolSettings) -> None:
        self.settings: MySwapPoolSettings = settings

        self.total_lp_supply: Optional[decimal.Decimal] = None
        self.token_amounts: Optional[src.helpers.TokenValues] = None

    async def get_data(self) -> None:
        self.total_lp_supply = decimal.Decimal(
            (
                await src.blockchain_call.func_call(
                    addr=self.settings.address,
                    selector="get_total_shares",
                    calldata=[self.settings.myswap_id],
                )
            )[0]
        )
        self.token_amounts = src.helpers.TokenValues()
        # The order of the values returned is: `name`, `token_a_address`, `token_a_reserves`, ``, `token_b_address`,
        # `token_b_reserves`, ``, `fee_percentage`, `cfmm_type`, `liq_token`.
        pool = await src.blockchain_call.func_call(
            addr=self.settings.address,
            selector="get_pool",
            calldata=[self.settings.myswap_id],
        )
        assert self.settings.token_1 == src.helpers.add_leading_zeros(hex(pool[1]))
        assert self.settings.token_2 == src.helpers.add_leading_zeros(hex(pool[4]))
        self.token_amounts.values[src.helpers.get_symbol(self.settings.token_1)] = decimal.Decimal(pool[2])
        self.token_amounts.values[src.helpers.get_symbol(self.settings.token_2)] = decimal.Decimal(pool[5])


class LPTokenPools:
    """
    This class initializes all JediSwap and MySwap pools configured in `JEDISWAP_POOL_SETTINGS` and 
    `MYSWAP_POOL_SETTINGS` and collects the total supply of LP tokens and the amounts of both tokens in each pool.
    """

    def __init__(self) -> None:
        self.pools: dict[str, Union[JediSwapPool, MySwapPool]] = {
            pool_symbol: JediSwapPool(settings=pool_settings)
            for pool_symbol, pool_settings in JEDISWAP_POOL_SETTINGS.items()
        }
        self.pools.update(
            {
                pool_symbol: MySwapPool(settings=pool_settings)
                for pool_symbol, pool_settings in MYSWAP_POOL_SETTINGS.items()
            }
        )

    async def get_data(self) -> None:
        for pool in self.pools.values():
            await pool.get_data()


def _get_lp_token_price(
    pool: Union[JediSwapPool, MySwapPool],
    prices: src.helpers.TokenValues,
) -> decimal.Decimal:
    token_1 = src.helpers.get_symbol(pool.settings.token_1)
    token_2 = src.helpers.get_symbol(pool.settings.token_2)
    token_1_value = (
        pool.token_amounts.values[token_1]
        / src.settings.TOKEN_SETTINGS[token_1].decimal_factor
        * prices.values[token_1]
    )
    token_2_value = (
        pool.token_amounts.values[token_2] 
        / src.settings.TOKEN_SETTINGS[token_2].decimal_factor
        * prices.values[token_2]
    )
    return (
        (token_1_value + token_2_value) 
        / (
            pool.total_lp_supply 
            / src.hashstack_v1.HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS[pool.settings.symbol].decimal_factor
        )
    )


class Prices:

    def __init__(self):
        # TODO: Move this mapping to `src.settings.TOKEN_SETTINGS`.
        self.tokens = [
            ("ethereum", "ETH"),
            ("bitcoin", "wBTC"),
            ("usd-coin", "USDC"),
            ("dai", "DAI"),
            ("tether", "USDT"),
            ("wrapped-steth", "wstETH"),
       ]
        self.vs_currency = "usd"
        self.prices: src.helpers.TokenValues = src.helpers.TokenValues()
        self.get_prices()

    def get_prices(self):
        token_ids = ""
        for token in self.tokens:
            token_ids += f"{token[0]},"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_ids}&vs_currencies={self.vs_currency}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for token in self.tokens:
                (id, symbol) = token
                self.prices.values[symbol] = decimal.Decimal(data[id][self.vs_currency])
        else:
            raise Exception(f"Failed getting prices, status code = {response.status_code}.")

    async def get_lp_token_prices(self) -> None:
        lp_token_pools = LPTokenPools()
        await lp_token_pools.get_data()
        for lp_token, lp_token_pool in lp_token_pools.pools.items():
            self.prices.values[lp_token] = _get_lp_token_price(pool=lp_token_pool, prices=self.prices)


@dataclasses.dataclass
class SwapAmmToken(src.settings.TokenSettings):
    # TODO: Improve this.
    balance_base: Optional[float] = None
    balance_converted: Optional[float] = None


class Pair:
    def tokens_to_id(self, t1, t2):
        (first, second) = tuple(sorted((t1, t2)))
        return f"{first}/{second}"


class Pool(Pair):
    def __init__(self, symbol1, symbol2, addresses, myswap_id):
        self.id = self.tokens_to_id(symbol1, symbol2)
        self.addresses = addresses
        t1 = SwapAmmToken(
            symbol=src.settings.TOKEN_SETTINGS[symbol1].symbol,
            decimal_factor=src.settings.TOKEN_SETTINGS[symbol1].decimal_factor,
            address=src.settings.TOKEN_SETTINGS[symbol1].address,
        )
        t2 = SwapAmmToken(
            symbol=src.settings.TOKEN_SETTINGS[symbol2].symbol,
            decimal_factor=src.settings.TOKEN_SETTINGS[symbol2].decimal_factor,
            address=src.settings.TOKEN_SETTINGS[symbol2].address,
        )
        setattr(self, symbol1, t1)
        setattr(self, symbol2, t2)
        self.tokens = [t1, t2]
        self.myswap_id = myswap_id

    async def get_balance(self):
        if self.myswap_id is not None:
            myswap_pool = await src.blockchain_call.get_myswap_pool(self.myswap_id)
        for token in self.tokens:
            balance = 0
            for address in self.addresses:
                balance += await src.blockchain_call.balance_of(token.address, address)
            if self.myswap_id is not None:
                balance += myswap_pool[token.symbol.upper()]
            token.balance_base = balance
            token.balance_converted = decimal.Decimal(balance) / token.decimal_factor

    def update_converted_balance(self):
        for token in self.tokens:
            token.balance_converted = decimal.Decimal(token.balance_base) / token.decimal_factor

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
        const = decimal.Decimal(buy.balance_base) * \
            decimal.Decimal(sell.balance_base)
        new_buy = buy.balance_base - amount
        new_sell = const / decimal.Decimal(new_buy)
        tokens_paid = round(new_sell - sell.balance_base)
        buy.balance_base = new_buy
        sell.balance_base = new_sell
        self.update_converted_balance()
        return tokens_paid

    def supply_at_price(self, initial_price: decimal.Decimal):
        # assuming constant product function
        constant = self.tokens[0].balance_converted * self.tokens[1].balance_converted
        return (initial_price * constant) ** decimal.Decimal("0.5") * (
            decimal.Decimal("1") -
            decimal.Decimal("0.95") ** decimal.Decimal("0.5")
        )


class SwapAmm(Pair):
    async def init(self):
        self.pools = {}
        # TODO: add wstETH pools
        self.add_pool(
            "ETH",
            "USDC",
            [
                "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",  # jediswap
                "0x030615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f",  # sithswap
                "0x000023c72abdf49dffc85ae3ede714f2168ad384cc67d08524732acea90df325",  # 10kswap
                "0x010884171baf1914edc28d7afb619b40a4051cfae78a094a55d230f19e944a28",  # myswap
            ],
            1
        )
        self.add_pool(
            "DAI",
            "ETH",
            [
                "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",  # jediswap
                "0x0032ebb8e68553620b97b308684babf606d9556d5c0a652450c32e85f40d000d",  # sithswap
                "0x017e9e62c04b50800d7c59454754fe31a2193c9c3c6c92c093f2ab0faadf8c87",  # 10kswap
            ],
            2
        )
        self.add_pool(
            "ETH",
            "USDT",
            [
                "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",  # jediswap
                "0x00691fa7f66d63dc8c89ff4e77732fff5133f282e7dbd41813273692cc595516",  # sithswap
                "0x05900cfa2b50d53b097cb305d54e249e31f24f881885aae5639b0cd6af4ed298",  # 10kswap
            ],
            4
        )
        self.add_pool(
            "wBTC",
            "ETH",
            [
                "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",  # jediswap
                "0x02a6e0ecda844736c4803a385fb1372eff458c365d2325c7d4e08032c7a908f3",  # 10kswap
            ]
        )
        self.add_pool(
            "wBTC",
            "USDC",
            [
                "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",  # jediswap
                "0x022e45d94d5c6c477d9efd440aad71b2c02a5cd5bed9a4d6da10bb7c19fd93ba",  # 10kswap
            ],
            3
        )
        self.add_pool(
            "wBTC",
            "USDT",
            [
                "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",  # jediswap
                "0x050031010bcee2f43575b3afe197878e064e1a03c12f2ff437f29a2710e0b6ef",  # 10kswap
            ]
        )
        self.add_pool(
            "DAI",
            "wBTC",
            [
                "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",  # jediswap
                "0x00f9d8f827734f5fd54571f0e78398033a3c1f1074a471cd4623f2aa45163718",  # 10kswap
            ]
        )
        self.add_pool(
            "DAI",
            "USDC",
            [
                "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",  # jediswap
                "0x015e9cd2d4d6b4bb9f1124688b1e6bc19b4ff877a01011d28c25c9ee918e83e5",  # sithswap
                "0x02e767b996c8d4594c73317bb102c2018b9036aee8eed08ace5f45b3568b94e5",  # 10kswap
            ],
            6
        )
        self.add_pool(
            "DAI",
            "USDT",
            [
                "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",  # jediswap
                "0x041d52e15e82b003bf0ad52ca58393c87abef3e00f1bf69682fd4162d5773f8f",  # 10kswap
            ]
        )
        self.add_pool(
            "USDC",
            "USDT",
            [
                "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",  # jediswap
                "0x0601f72228f73704e827de5bcd8dadaad52c652bb1e42bf492d90bbe22df2cec",  # sithswap
                "0x041a708cf109737a50baa6cbeb9adf0bf8d97112dc6cc80c7a458cbad35328b0",  # 10kswap
            ],
            5
        )
        await self.get_balance()

    async def get_balance(self):
        for pool in self.pools.values():
            await pool.get_balance()

    def add_pool(self, t1, t2, addresses, myswap_id=None):
        pool = Pool(t1, t2, addresses, myswap_id)
        self.pools[pool.id] = pool

    def get_pool(self, t1, t2):
        try:
            return self.pools[self.tokens_to_id(t1, t2)]
        except:
            raise Exception(
                f"Trying to get pool that is not set: {self.tokens_to_id(t1, t2)}"
            )


def get_supply_at_price(
    collateral_token: str,
    collateral_token_price: decimal.Decimal,
    debt_token: str,
    swap_amms: SwapAmm,
) -> decimal.Decimal:
    return swap_amms.get_pool(collateral_token, debt_token).supply_at_price(collateral_token_price)