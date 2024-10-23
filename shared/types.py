from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class BaseTokenParameters:
    address: str
    decimals: int
    symbol: str
    underlying_symbol: str
    underlying_address: str


class TokenParameters(defaultdict):
    """
    A class that describes the parameters of collateral or debt tokens. These parameters are e.g. the token address,
    symbol, decimals, underlying token symbol, etc.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            lambda: BaseTokenParameters(
                address="",
                decimals=0,
                symbol="",
                underlying_symbol="",
                underlying_address="",
            ),
            *args[1:],
            **kwargs,
        )


@dataclass
class TokenSettings:
    symbol: str
    # Source: Starkscan, e.g.
    # https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
    decimal_factor: Decimal
    address: str