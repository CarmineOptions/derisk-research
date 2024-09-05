import collections
import dataclasses
import decimal


@dataclasses.dataclass
class BaseTokenParameters:
    address: str
    decimals: int
    symbol: str
    underlying_symbol: str
    underlying_address: str


@dataclasses.dataclass
class ZkLendCollateralTokenParameters(BaseTokenParameters):
    collateral_factor: float
    liquidation_bonus: float


@dataclasses.dataclass
class ZkLendDebtTokenParameters(BaseTokenParameters):
    debt_factor: float


class InterestRateModels(collections.defaultdict):
    """
    A class that describes the state of the interest rate indices for multiple tokens. The indices help transform face
    amounts into raw amounts. The raw amount is the amount that would have been accumulated into the face amount if it
    were deposited at genesis.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(lambda: decimal.Decimal("1"), *args[1:], **kwargs)


class TokenParameters(collections.defaultdict):
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


class ZkLendCollateralEnabled(collections.defaultdict):
    """A class that describes which tokens are eligible to be counted as collateral."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(lambda: False, *args[1:], **kwargs)


class Prices(collections.defaultdict):
    """A class that describes the prices of tokens."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(lambda: None, *args[1:], **kwargs)


class CollateralAndDebtInterestRateModels:
    """
    A class that describes the state of the collateral and debt interest rate indices for multiple tokens. The indices
    help transform face amounts into raw amounts. The raw amount is the amount that would have been accumulated into
    the face amount if it were deposited at genesis.
    """

    def __init__(self) -> None:
        # These models reflect the interest rates at which users lend/stake funds.
        self.collateral: InterestRateModels = InterestRateModels()
        # These models reflect the interest rates at which users borrow funds.
        self.debt: InterestRateModels = InterestRateModels()


class CollateralAndDebtTokenParameters:
    """
    A class that describes the parameters of collateral and debt tokens. These parameters are e.g. the token address,
    symbol, decimals, underlying token symbol, etc.
    """

    def __init__(self) -> None:
        self.collateral: TokenParameters = TokenParameters()
        self.debt: TokenParameters = TokenParameters()
