from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Union

from shared.constants import TOKEN_SETTINGS


@dataclass
class TokenSettings:
    symbol: str
    # Source: Starkscan, e.g.
    # https://starkscan.co/token/0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 for ETH.
    decimal_factor: float
    address: str


class TokenValues:
    def __init__(
        self,
        values: Optional[dict[str, Union[bool, Decimal]]] = None,
        # TODO: Only one parameter should be specified..
        init_value: Decimal = Decimal("0"),
    ) -> None:
        if values:
            # Nostra Mainnet can contain different tokens that aren't mentioned in `TOKEN_SETTINGS`
            # assert set(values.keys()) == set(TOKEN_SETTINGS.keys())
            self.values: dict[str, Decimal] = values
        else:
            self.values: dict[str, Decimal] = {
                token: init_value for token in TOKEN_SETTINGS
            }


def add_leading_zeros(hash: str) -> str:
    """
    Converts e.g. `0x436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e` to
    `0x00436d8d078de345c11493bd91512eae60cd2713e05bcaa0bb9f0cba90358c6e`.
    """
    return "0x" + hash[2:].zfill(64)
