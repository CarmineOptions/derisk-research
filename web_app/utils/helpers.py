import logging
import os
from decimal import Decimal
from typing import Iterator, Union

import google.cloud.storage
import pandas as pd

from utils.settings import TOKEN_SETTINGS


class TokenValues:
    """A class that holds all token values"""

    def __init__(
        self,
        values: dict[str, Union[bool, Decimal]] | None = None,
        init_value: Decimal = Decimal("0"),
    ) -> None:
        if values:
            assert set(values.keys()) == set(TOKEN_SETTINGS.keys())
            self.values: dict[str, Decimal] = values
        else:
            self.values: dict[str, Decimal] = {
                token: init_value for token in TOKEN_SETTINGS
            }


MAX_ROUNDING_ERRORS: TokenValues = TokenValues(
    values={
        "ETH": Decimal("0.5e13"),
        "wBTC": Decimal("1e2"),
        "USDC": Decimal("1e4"),
        "DAI": Decimal("1e16"),
        "USDT": Decimal("1e4"),
        "wstETH": Decimal("0.5e13"),
        "LORDS": Decimal("0.5e13"),
        "STRK": Decimal("0.5e13"),
    },
)


class Portfolio(TokenValues):
    """A class that describes holdings of tokens."""

    MAX_ROUNDING_ERRORS: TokenValues = MAX_ROUNDING_ERRORS

    def __init__(self) -> None:
        super().__init__(init_value=Decimal("0"))


def get_symbol(address: str) -> str:
    """
    Returns the symbol of a given address.
    :param address: the address of the symbol
    :return: str
    """
    n = int(address, base=16)
    symbol_address_map = {
        token: token_settings.address
        for token, token_settings in TOKEN_SETTINGS.items()
    }

    for symbol, addr in symbol_address_map.items():
        if int(addr, base=16) == n:
            return symbol

    raise KeyError(f"Address = {address} does not exist in the symbol table.")
