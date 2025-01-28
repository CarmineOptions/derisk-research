from collections import defaultdict
from dataclasses import dataclass

from shared.custom_types import BaseTokenParameters


class ZkLendCollateralEnabled(defaultdict):
    """A class that describes which tokens are eligible to be counted as collateral."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(lambda: False, *args[1:], **kwargs)


@dataclass
class ZkLendCollateralTokenParameters(BaseTokenParameters):
    collateral_factor: float
    liquidation_bonus: float


@dataclass
class ZkLendDebtTokenParameters(BaseTokenParameters):
    debt_factor: float
