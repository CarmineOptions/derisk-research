"""
Module for handling Swap AMM pools, including Pool, Pair, 
and MySwapPool classes for liquidity and balance operations.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from data_handler.handlers.blockchain_call import balance_of, func_call, get_myswap_pool

from shared.constants import TOKEN_SETTINGS
from shared.helpers import add_leading_zeros
from shared.custom_types import TokenSettings, TokenValues


class Pair:
    """
    Utility class for handling token pairs in pools.
    """
    @staticmethod
    def tokens_to_id(base_token, quote_token):
        """
        Generate a unique pool ID by combining two token symbols.
        """
        (first, second) = tuple(sorted((base_token, quote_token)))
        return f"{first}/{second}"


class Pool(Pair):
    """
    Represents a liquidity pool, inheriting from Pair and providing balance and supply operations.
    """
    def __init__(self, symbol1, symbol2, addresses, myswap_id):
        self.id = Pair.tokens_to_id(symbol1, symbol2)
        self.addresses = addresses
        base_token = SwapAmmToken(
            symbol=TOKEN_SETTINGS[symbol1].symbol,
            decimal_factor=TOKEN_SETTINGS[symbol1].decimal_factor,
            address=TOKEN_SETTINGS[symbol1].address,
        )
        quote_token = SwapAmmToken(
            symbol=TOKEN_SETTINGS[symbol2].symbol,
            decimal_factor=TOKEN_SETTINGS[symbol2].decimal_factor,
            address=TOKEN_SETTINGS[symbol2].address,
        )
        setattr(self, symbol1, base_token)
        setattr(self, symbol2, quote_token)
        self.tokens = [base_token, quote_token]
        self.myswap_id = myswap_id

    async def get_balance(self):
        """
        Asynchronously fetches and updates token balances in the pool.
        """
        myswap_pool = None
        if self.myswap_id is not None:
            myswap_pool = await get_myswap_pool(self.myswap_id)
        for token in self.tokens:
            balance = 0
            if myswap_pool and token.symbol.upper() in myswap_pool:
                balance += myswap_pool[token.symbol.upper()]
            for address in self.addresses:
                balance += await balance_of(token.address, address)
            token.balance_base = balance
            token.balance_converted = Decimal(balance) / token.decimal_factor

    def update_converted_balance(self):
        """
        Update the converted balance for each token based on its decimal factor.
        """
        for token in self.tokens:
            token.balance_converted = Decimal(token.balance_base) / token.decimal_factor

    def supply_at_price(self, initial_price: Decimal):
        """
        Calculate supply available at a specified price, assuming constant product function.
        """
        # assuming constant product function
        constant = Decimal(self.tokens[0].balance_converted * self.tokens[1].balance_converted)
        return (initial_price * constant).sqrt() * (Decimal("1") - Decimal("0.95").sqrt())


class MySwapPool(Pool):
    """
    This class implements MySwap pools where Hashstack V1
      users can spend their debt. To properly account for their
    token holdings, we collect the total supply of LP 
    tokens and the amounts of both tokens in the pool.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize pools with predefined tokens and addresses, and fetch balances.
        """

        super().__init__(*args, **kwargs)

        self.total_lp_supply: Optional[Decimal] = None
        self.token_amounts: Optional[TokenValues] = None

    async def get_data(self) -> None:
        """ Collects the total supply of LP tokens and the amounts of both tokens in the pool. """
        self.total_lp_supply = Decimal(
            (
                await func_call(
                    addr=self.addresses[-1],
                    selector="get_total_shares",
                    calldata=[self.myswap_id],
                )
            )[0]
        )
        self.token_amounts = TokenValues()
        # The order of the values returned is: `name`, `token_a_address`, 
        # `token_a_reserves`, ``, `token_b_address`,
        # `token_b_reserves`, ``, `fee_percentage`, `cfmm_type`, `liq_token`.
        pool = await func_call(
            addr=self.addresses[-1],
            selector="get_pool",
            calldata=[self.myswap_id],
        )
        assert self.tokens[0].address == add_leading_zeros(hex(pool[1]))
        assert self.tokens[1].address == add_leading_zeros(hex(pool[4]))
        self.token_amounts.values[self.tokens[0].symbol] = Decimal(pool[2])
        self.token_amounts.values[self.tokens[1].symbol] = Decimal(pool[5])


@dataclass
class SwapAmmToken(TokenSettings):
    """ This class represents a token in the Swap AMM, with balance and conversion operations. """
    # TODO: Improve this.
    balance_base: Optional[float] = None
    balance_converted: Optional[float] = None


class SwapAmm(Pair):
    """ This class represents the Swap AMM, which contains pools and provides balance 
    and supply operations. """
    async def init(self):
        """ Initialize the SwapAmm with predefined pools and fetch balances. """
        # TODO: Add AVNU
        self.pools = {}
        self.add_pool(
            "ETH",
            "USDC",
            [
                "0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a",  # jediswap
                "0x030615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f",  # sithswap
                "0x000023c72abdf49dffc85ae3ede714f2168ad384cc67d08524732acea90df325",  # 10kswap
            ],
            1,
        )
        self.add_pool(
            "DAI",
            "ETH",
            [
                "0x07e2a13b40fc1119ec55e0bcf9428eedaa581ab3c924561ad4e955f95da63138",  # jediswap
                "0x0032ebb8e68553620b97b308684babf606d9556d5c0a652450c32e85f40d000d",  # sithswap
                "0x017e9e62c04b50800d7c59454754fe31a2193c9c3c6c92c093f2ab0faadf8c87",  # 10kswap
            ],
            2,
        )
        self.add_pool(
            "ETH",
            "USDT",
            [
                "0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6",  # jediswap
                "0x00691fa7f66d63dc8c89ff4e77732fff5133f282e7dbd41813273692cc595516",  # sithswap
                "0x05900cfa2b50d53b097cb305d54e249e31f24f881885aae5639b0cd6af4ed298",  # 10kswap
            ],
            4,
        )
        self.add_pool(
            "wBTC",
            "ETH",
            [
                "0x0260e98362e0949fefff8b4de85367c035e44f734c9f8069b6ce2075ae86b45c",  # jediswap
                "0x02a6e0ecda844736c4803a385fb1372eff458c365d2325c7d4e08032c7a908f3",  # 10kswap
            ],
        )
        self.add_pool(
            "wBTC",
            "USDC",
            [
                "0x005a8054e5ca0b277b295a830e53bd71a6a6943b42d0dbb22329437522bc80c8",  # jediswap
                "0x022e45d94d5c6c477d9efd440aad71b2c02a5cd5bed9a4d6da10bb7c19fd93ba",  # 10kswap
            ],
            3,
        )
        self.add_pool(
            "wBTC",
            "USDT",
            [
                "0x044d13ad98a46fd2322ef2637e5e4c292ce8822f47b7cb9a1d581176a801c1a0",  # jediswap
                "0x050031010bcee2f43575b3afe197878e064e1a03c12f2ff437f29a2710e0b6ef",  # 10kswap
            ],
        )
        self.add_pool(
            "DAI",
            "wBTC",
            [
                "0x039c183c8e5a2df130eefa6fbaa3b8aad89b29891f6272cb0c90deaa93ec6315",  # jediswap
                "0x00f9d8f827734f5fd54571f0e78398033a3c1f1074a471cd4623f2aa45163718",  # 10kswap
            ],
        )
        self.add_pool(
            "DAI",
            "USDC",
            [
                "0x00cfd39f5244f7b617418c018204a8a9f9a7f72e71f0ef38f968eeb2a9ca302b",  # jediswap
                "0x015e9cd2d4d6b4bb9f1124688b1e6bc19b4ff877a01011d28c25c9ee918e83e5",  # sithswap
                "0x02e767b996c8d4594c73317bb102c2018b9036aee8eed08ace5f45b3568b94e5",  # 10kswap
            ],
            6,
        )
        self.add_pool(
            "DAI",
            "USDT",
            [
                "0x00f0f5b3eed258344152e1f17baf84a2e1b621cd754b625bec169e8595aea767",  # jediswap
                "0x041d52e15e82b003bf0ad52ca58393c87abef3e00f1bf69682fd4162d5773f8f",  # 10kswap
            ],
        )
        self.add_pool(
            "USDC",
            "USDT",
            [
                "0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b",  # jediswap
                "0x0601f72228f73704e827de5bcd8dadaad52c652bb1e42bf492d90bbe22df2cec",  # sithswap
                "0x041a708cf109737a50baa6cbeb9adf0bf8d97112dc6cc80c7a458cbad35328b0",  # 10kswap
            ],
            5,
        )
        self.add_pool(
            "STRK",
            "USDC",
            [
                "0x05726725e9507c3586cc0516449e2c74d9b201ab2747752bb0251aaa263c9a26",  # jediswap
                "0x00900978e650c11605629fc3eda15447d57e884431894973e4928d8cb4c70c24",  # sithswap
                "0x066733193503019e4e9472f598ff32f15951a0ddb8fb5001f0beaa8bd1fb6840",  # 10kswap
            ],
            None,
        )
        self.add_pool(
            "STRK",
            "USDT",
            [
                "0x0784a8ec64af2b45694b94875fe6adbb57fadf9e196aa1aa1d144d163d0d8c51",  # 10kswap
            ],
            None,
        )
        self.add_pool(
            "DAI",
            "STRK",
            [
                "0x048ddb56ceb74777d081a9ce684aaa78e98c286e14fc1badb3a9938e710d6866",  # jediswap
            ],
            None,
        )
        await self.get_balance()

    async def get_balance(self):
        """
        Asynchronously retrieves balances for all pools.
        """
        for pool in self.pools.values():
            await pool.get_balance()

    def add_pool(self, base_token: str, quote_token, pool_addresses, myswap_id=None):
        """
        Add a new pool to the SwapAmm with the specified tokens and addresses.
        """
        if myswap_id is None:
            pool = Pool(base_token, quote_token, pool_addresses, myswap_id)
        else:
            pool = MySwapPool(base_token, quote_token, pool_addresses, myswap_id)
        self.pools[pool.id] = pool

    def get_pool(self, base_token, quote_token):
        """
        Retrieve a pool by base and quote token, raising an error if not found.
        """
        pools = self.pools.get(self.tokens_to_id(base_token, quote_token), None)
        if not pools:
            raise ValueError(
                f"Trying to get pools that are not set: "
                f"{self.tokens_to_id(base_token, quote_token)}"
            )
        return pools

    def get_supply_at_price(
        self,
        collateral_token_underlying_symbol: str,
        collateral_token_price: float,
        debt_token_underlying_symbol: str,
        amm: str,
    ) -> float:
        """
        Get the supply at a given price in a given AMM.
        """
        pool: Pool = self.get_pool(
            token_a=collateral_token_underlying_symbol,
            token_b=debt_token_underlying_symbol,
        )
        return pool.supply_at_price(
            initial_price=collateral_token_price,
            amm=amm,
        )
