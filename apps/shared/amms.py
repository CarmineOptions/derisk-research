"""  AMMS module for managing liquidity pools and automated market makers. """

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

from shared.blockchain_call import balance_of, func_call, get_myswap_pool
from shared.constants import POOL_MAPPING, TOKEN_SETTINGS
from shared.helpers import add_leading_zeros
from shared.custom_types import TokenSettings, TokenValues


class Pair:
    """A class to represent a pair of tokens and generate a unique ID for them.

    Methods
    -------
    tokens_to_id(base_token: str, quote_token: str) -> str
        Generate a unique ID for a pair of tokens by sorting
        them alphabetically and combining them with a slash.
    """

    @staticmethod
    def tokens_to_id(base_token: str, quote_token: str) -> str:
        """
        Generate a unique ID for a pair of tokens by
        sorting them alphabetically and combining them with a slash.

        :param base_token: The symbol of the base token.
        :param quote_token: The symbol of the quote token.
        :return: A string ID representing the token pair.
        """
        (first, second) = tuple(sorted((base_token, quote_token)))
        return f"{first}/{second}"


class Pool(Pair):
    """Pool class for managing liquidity pools with two tokens."""

    def __init__(
        self, symbol1: str, symbol2: str, addresses: List[str], myswap_id: Optional[int]
    ) -> None:
        """
        Initialize a Pool instance for managing liquidity pools with two tokens.

        :param symbol1: The symbol for the first token in the pair.
        :param symbol2: The symbol for the second token in the pair.
        :param addresses: A list of blockchain addresses associated with the pool.
        :param myswap_id: An optional identifier for MySwap pools.
        """
        self.id = Pair.tokens_to_id(symbol1, symbol2)
        self.addresses = addresses
        self.myswap_id = myswap_id

        base_token_info = TOKEN_SETTINGS.get(symbol1)
        quote_token_info = TOKEN_SETTINGS.get(symbol2)
        if not base_token_info or not quote_token_info:
            self.tokens = []
            return

        base_token = SwapAmmToken(
            symbol=base_token_info.symbol,
            decimal_factor=base_token_info.decimal_factor,
            address=base_token_info.address,
        )
        quote_token = SwapAmmToken(
            symbol=quote_token_info.symbol,
            decimal_factor=quote_token_info.decimal_factor,
            address=quote_token_info.address,
        )
        setattr(self, symbol1, base_token)
        setattr(self, symbol2, quote_token)
        self.tokens = [base_token, quote_token]

    async def get_balance(self) -> None:
        """
        Retrieve the balance for each token in the pool,
        updating both the base and converted balances.
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

    def update_converted_balance(self) -> None:
        """
        Recalculate and update the converted balance for each token based on its base balance.
        """
        for token in self.tokens:
            token.balance_converted = Decimal(token.balance_base) / token.decimal_factor

    def supply_at_price(self, initial_price: Decimal) -> Decimal:
        """
        Calculate the supply of a token at a given price using a constant product formula.

        :param initial_price: The initial price at which to calculate the supply.
        :return: The calculated supply based on the initial price.
        """
        constant = Decimal(
            self.tokens[0].balance_converted * self.tokens[1].balance_converted
        )
        return (initial_price * constant).sqrt() * (
            Decimal("1") - Decimal("0.95").sqrt()
        )


class MySwapPool(Pool):
    """
    Implements MySwap pools where users can utilize debt in Hashstack V1.
    Tracks LP token supply and individual token amounts in the pool.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.total_lp_supply: Optional[Decimal] = None
        self.token_amounts: Optional[TokenValues] = None

    async def get_data(self) -> None:
        """
        Retrieve pool data, including the total supply of
        LP tokens and reserves of each token in the pool.
        """
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
    """SwapAmmToken class for managing token settings and balances."""

    balance_base: Optional[float] = None  # Base balance for the token.
    balance_converted: Optional[float] = None  # Converted balance for the token.


class SwapAmm(Pair):
    """SwapAmm class for managing multiple liquidity pools."""

    def __init__(self) -> None:
        """
        Initialize a SwapAmm instance for managing multiple liquidity pools.
        """
        self.pools: Dict[str, Pool] = {}
        self.add_all_pools()

    def add_all_pools(self) -> None:
        """
        Add all predefined pools based on configuration in POOL_MAPPING.
        """
        for pool_name, pool_data in POOL_MAPPING.items():
            self.add_pool(
                base_token=pool_data["base_token"],
                quote_token=pool_data["quote_token"],
                pool_addresses=pool_data["addresses"],
                myswap_id=pool_data.get("myswap_id"),
            )

    async def get_balance(self) -> None:
        """
        Retrieve balances for each pool's tokens asynchronously.
        """
        for pool in self.pools.values():
            await pool.get_balance()

    def add_pool(
        self,
        base_token: str,
        quote_token: str,
        pool_addresses: List[str],
        myswap_id: Optional[int] = None,
    ) -> None:
        """
        Add a new liquidity pool for a token pair to the SwapAmm instance.

        :param base_token: The symbol for the base token in the pair.
        :param quote_token: The symbol for the quote token in the pair.
        :param pool_addresses: A list of addresses associated with the pool.
        :param myswap_id: Optional identifier for MySwap pools.
        """
        if myswap_id is None:
            pool = Pool(base_token, quote_token, pool_addresses, myswap_id)
        else:
            pool = MySwapPool(base_token, quote_token, pool_addresses, myswap_id)
        self.pools[pool.id] = pool

    def get_pool(self, base_token: str, quote_token: str) -> Pool:
        """
        Retrieve a pool instance for a specific token pair.

        :param base_token: The symbol of the base token.
        :param quote_token: The symbol of the quote token.
        :return: The Pool instance associated with the token pair.
        :raises ValueError: If the requested pool is not found.
        """
        pool_id = self.tokens_to_id(base_token, quote_token)
        pool = self.pools.get(pool_id)
        if not pool:
            raise ValueError(f"Trying to get pools that are not set: {pool_id}")
        return pool

    def get_supply_at_price(
        self,
        collateral_token_underlying_symbol: str,
        collateral_token_price: float,
        debt_token_underlying_symbol: str,
        amm: str,
    ) -> float:
        """
        Get the supply at a given price for a specified AMM.

        :param collateral_token_underlying_symbol: The symbol for the collateral token.
        :param collateral_token_price: The price of the collateral token.
        :param debt_token_underlying_symbol: The symbol for the debt token.
        :param amm: The Automated Market Maker (AMM) to use.
        :return: The calculated supply at the specified price.
        """
        pool: Pool = self.get_pool(
            base_token=collateral_token_underlying_symbol,
            quote_token=debt_token_underlying_symbol,
        )
        return pool.supply_at_price(initial_price=Decimal(collateral_token_price))
