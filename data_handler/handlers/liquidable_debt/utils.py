from decimal import Decimal
from dataclasses import dataclass

import requests
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call

from handlers.helpers import TokenValues, get_symbol, add_leading_zeros
from handlers.settings import (TOKEN_SETTINGS, TokenSettings,
                               HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS, JEDISWAP_POOL_SETTINGS,
                               MySwapPoolSettings, MYSWAP_POOL_SETTINGS)

NET = FullNodeClient(node_url="https://starknet-mainnet.public.blastapi.io")


async def balance_of(token_addr, holder_addr):
    res = await func_call(
        int(token_addr, base=16), "balanceOf", [int(holder_addr, base=16)]
    )
    return res[0]


async def func_call(addr, selector, calldata):
    call = Call(
        to_addr=addr, selector=get_selector_from_name(selector), calldata=calldata
    )
    try:
        res = await NET.call_contract(call)
    except:
        time.sleep(10)
        res = await NET.call_contract(call)
    return res


class JediSwapPool:
    """
    This class implements JediSwap pools where Hashstack V1 users can spend their debt. To properly account for their
    token holdings, we collect the total supply of LP tokens and the amounts of both tokens in the pool.
    """

    def __init__(self, settings: JediSwapPoolSettings) -> None:
        self.settings: JediSwapPoolSettings = settings

        self.total_lp_supply: Decimal | None = None
        self.token_amounts: TokenValues | None = None

    async def get_data(self) -> None:
        self.total_lp_supply = Decimal(
            (
                await func_call(
                    addr=self.settings.address,
                    selector='totalSupply',
                    calldata=[],
                )
            )[0]
        )
        self.token_amounts = TokenValues()
        for token in [self.settings.token_1, self.settings.token_2]:
            self.token_amounts.values[get_symbol(token)] = Decimal(
                await balance_of(
                    token_addr=token,
                    holder_addr=self.settings.address,
                )
            )


class MySwapPool:
    """
    This class implements MySwap pools where Hashstack V1 users can spend their debt. To properly account for their
    token holdings, we collect the total supply of LP tokens and the amounts of both tokens in the pool.
    """

    def __init__(self, settings: MySwapPoolSettings) -> None:
        self.settings: MySwapPoolSettings = settings

        self.total_lp_supply: Decimal | None = None
        self.token_amounts: TokenValues | None = None

    async def get_data(self) -> None:
        self.total_lp_supply = Decimal(
            (
                await func_call(
                    addr=self.settings.address,
                    selector="get_total_shares",
                    calldata=[self.settings.myswap_id],
                )
            )[0]
        )
        self.token_amounts = TokenValues()
        # The order of the values returned is: `name`, `token_a_address`, `token_a_reserves`, ``, `token_b_address`,
        # `token_b_reserves`, ``, `fee_percentage`, `cfmm_type`, `liq_token`.
        pool = await func_call(
            addr=self.settings.address,
            selector="get_pool",
            calldata=[self.settings.myswap_id],
        )
        assert self.settings.token_1 == add_leading_zeros(hex(pool[1]))
        assert self.settings.token_2 == add_leading_zeros(hex(pool[4]))
        self.token_amounts.values[get_symbol(self.settings.token_1)] = Decimal(pool[2])
        self.token_amounts.values[get_symbol(self.settings.token_2)] = Decimal(pool[5])


class LPTokenPools:
    """
    This class initializes all JediSwap and MySwap pools configured in `JEDISWAP_POOL_SETTINGS` and
    `MYSWAP_POOL_SETTINGS` and collects the total supply of LP tokens and the amounts of both tokens in each pool.
    """

    def __init__(self) -> None:
        self.pools: dict[str, JediSwapPool | MySwapPool] = {
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


class Prices:

    def __init__(self):
        self.tokens = [
            ("ethereum", "ETH"),
            ("bitcoin", "wBTC"),
            ("usd-coin", "USDC"),
            ("dai", "DAI"),
            ("tether", "USDT"),
            ("wrapped-steth", "wstETH"),
            ("lords", "LORDS"),
            ("starknet", "STRK"),
        ]
        self.vs_currency = "usd"
        self.prices: TokenValues = TokenValues()
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
                self.prices.values[symbol] = Decimal(data[id][self.vs_currency])
        else:
            raise Exception(f"Failed getting prices, status code = {response.status_code}.")

    async def get_lp_token_prices(self) -> None:
        lp_token_pools = LPTokenPools()
        await lp_token_pools.get_data()
        for lp_token, lp_token_pool in lp_token_pools.pools.items():
            self.prices.values[lp_token] = self._get_lp_token_price(pool=lp_token_pool, prices=self.prices)

    @staticmethod
    def _get_lp_token_price(
            pool: JediSwapPool | MySwapPool,
            prices: TokenValues,
    ) -> Decimal:
        token_1 = get_symbol(pool.settings.token_1)
        token_2 = get_symbol(pool.settings.token_2)
        token_1_value = (
                pool.token_amounts.values[token_1]
                / TOKEN_SETTINGS[token_1].decimal_factor
                * prices.values[token_1]
        )
        token_2_value = (
                pool.token_amounts.values[token_2]
                / TOKEN_SETTINGS[token_2].decimal_factor
                * prices.values[token_2]
        )
        return (
                (token_1_value + token_2_value)
                / (
                        pool.total_lp_supply
                        / HASHSTACK_V1_ADDITIONAL_TOKEN_SETTINGS[
                            pool.settings.symbol
                        ].decimal_factor
                )
        )
