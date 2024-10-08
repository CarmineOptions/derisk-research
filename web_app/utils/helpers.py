import logging
import os
from decimal import Decimal
from typing import Iterator, Union

import google.cloud.storage
import pandas as pd
from utils.exceptions import TokenValidationError
from utils.settings import TOKEN_SETTINGS


class TokenValues:
    """A class that holds all token values"""

    def __init__(
        self,
        values: dict[str, Union[bool, Decimal]] | None = None,
        init_value: Decimal = Decimal("0"),
    ) -> None:
        if values:
            self._validate_token_values(values)
            self.values: dict[str, Decimal] = values
        else:
            self.values: dict[str, Decimal] = {
                token: init_value for token in TOKEN_SETTINGS
            }

    @staticmethod
    def _validate_token_values(token_values: dict[str, Union[bool, Decimal]]) -> None:
        """
        Validate's token_values keys
        :param token_values: dict[str, Union[bool, Decimal]]
        :return: None
        """
        if set(token_values.keys()) != set(TOKEN_SETTINGS.keys()):
            raise TokenValidationError(
                "Token values keys do not match with TOKEN_SETTINGS keys"
            )


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
    address_int = int(address, base=16)

    for symbol, settings in TOKEN_SETTINGS.items():
        if int(settings.address, base=16) == address_int:
            return symbol

    raise KeyError(f"Address = {address} does not exist in the symbol table.")
