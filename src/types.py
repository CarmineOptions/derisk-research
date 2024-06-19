# TODO: split this into multiple modules
import abc
import collections
import dataclasses
import decimal



class InterestRateModels(collections.defaultdict):
    """
    A class that describes the state of the interest rate indices for multiple tokens. The indices help transform face 
    amounts into raw amounts. The raw amount is the amount that would have been accumulated into the face amount if it 
    were deposited at genesis.
    """

    def __init__(self) -> None:
        super().__init__(lambda: decimal.Decimal("1"))


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


# TODO: Rounding errors?
# TODO: Relevant interest rate models?
@dataclasses.dataclass
class BaseTokenParameters:
    address: str
    decimals: int
    symbol: str
    underlying_symbol: str
    underlying_address: str


class TokenParameters(collections.defaultdict):
    """
    A class that describes the parameters of collateral or debt tokens. These parameters are e.g. the token address,
    symbol, decimals, underlying token symbol, etc.
    """

    def __init__(self) -> None:
        super().__init__(
            lambda: BaseTokenParameters(
                address='',
                decimal=0,
                symbol='',
                underlying_symbol='',
                underlying_address='',
            ),
        )


class CollateralAndDebtTokenParameters:
    """
    A class that describes the parameters of collateral and debt tokens. These parameters are e.g. the token address,
    symbol, decimals, underlying token symbol, etc.
    """

    def __init__(self) -> None:
        self.collateral: TokenParameters = TokenParameters()  # TODO: add `collateral_factor``
        self.debt: TokenParameters = TokenParameters()  # TODO: add `debt_factor`


class Portfolio(collections.defaultdict):
    """A class that describes holdings of tokens."""

    # TODO: Update the values.
    MAX_ROUNDING_ERRORS: collections.defaultdict = collections.defaultdict(
        lambda: decimal.Decimal("5e12"),
        **{
            "ETH": decimal.Decimal("5e12"),
            "WBTC": decimal.Decimal("1e2"),
            "USDC": decimal.Decimal("1e4"),
            "DAI": decimal.Decimal("1e16"),
            "USDT": decimal.Decimal("1e4"),
            "wstETH": decimal.Decimal("5e12"),
            "LORDS": decimal.Decimal("5e12"),
            "STRK": decimal.Decimal("5e12"),
        },
    )

    def __init__(self, **kwargs) -> None:
        assert all(isinstance(x, str) for x in kwargs.keys())
        assert all(isinstance(x, decimal.Decimal) for x in kwargs.values())
        super().__init__(decimal.Decimal, **kwargs)

    def __add__(self, second_portfolio: 'Portfolio') -> 'Portfolio':
        if not isinstance(second_portfolio, Portfolio):
            raise TypeError(f"Cannot add {type(second_portfolio)} to Portfolio.")
        new_portfolio = Portfolio()
        for token, amount in self.items():
            new_portfolio[token] += amount
        for token, amount in second_portfolio.items():
            new_portfolio[token] += amount
        return new_portfolio

    # TODO: Find a better solution to fix the discrepancies.
    def round_small_value_to_zero(self, token: str):
        if abs(self[token]) < self.MAX_ROUNDING_ERRORS[token]:
            self[token] = decimal.Decimal("0")

    def increase_value(self, token: str, value: decimal.Decimal):
        self[token] += value
        self.round_small_value_to_zero(token=token)

    def set_value(self, token: str, value: decimal.Decimal):
        self[token] = value
        self.round_small_value_to_zero(token=token)


class Prices(collections.defaultdict):
    """ A class that describes the prices of tokens. """

    def __init__(self) -> None:
        super().__init__(lambda: None)


class LoanEntity(abc.ABC):
    """
    A class that describes and entity which can hold collateral, borrow debt and be liquidable. For example, on 
    Starknet, such an entity is the user in case of zkLend, Nostra Alpha and Nostra Mainnet, or an individual loan in 
    case od Hashstack V0 and Hashstack V1.
    """

    # TOKEN_SETTINGS: dict[str, TokenSettings] = TOKEN_SETTINGS

    def __init__(self) -> None:
        self.collateral: Portfolio = Portfolio()
        self.debt: Portfolio = Portfolio()

    def compute_collateral_usd(
        self,
        risk_adjusted: bool,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels,
        prices: Prices,
    ) -> float:
        return sum(
            float(token_amount)
            / (10 ** collateral_token_parameters[token].decimals)
            * (collateral_token_parameters[token].collateral_factor if risk_adjusted else 1.0)
            * float(collateral_interest_rate_model[token])
            * prices[token]
            for token, token_amount in self.collateral.items()
        )

    def compute_debt_usd(
        self, 
        risk_adjusted: bool,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
        prices: Prices,
    ) -> float:
        return sum(
            float(token_amount)
            / (10 ** debt_token_parameters[token].decimals)
            / (debt_token_parameters[token].debt_factor if risk_adjusted else 1.0)
            * float(debt_interest_rate_model[token])
            * prices[token]
            for token, token_amount in self.debt.items()
        )

    @abc.abstractmethod
    def compute_health_factor(self):
        pass

    @abc.abstractmethod
    def compute_debt_to_be_liquidated(self):
        pass

    def get_collateral_str(
        self,
        collateral_token_parameters: TokenParameters,
        collateral_interest_rate_model: InterestRateModels,
    ) -> str:
        return ', '.join(
            f"{token}: {round(token_amount / (10 ** collateral_token_parameters[token].decimals) * collateral_interest_rate_model[token], 4)}"
            for token, token_amount in self.collateral.items()
            if token_amount > decimal.Decimal("0")
        )

    def get_debt_str(
        self,
        debt_token_parameters: TokenParameters,
        debt_interest_rate_model: InterestRateModels,
    ) -> str:
        return ', '.join(
            f"{token}: {round(token_amount / (10 ** debt_token_parameters[token].decimals) * debt_interest_rate_model[token], 4)}"
            for token, token_amount in self.debt.items()
            if token_amount > decimal.Decimal("0")
        )

    def has_collateral(self) -> bool:
        return any(token_amount for token_amount in self.collateral.values())

    def has_debt(self) -> bool:
        return any(token_amount for token_amount in self.debt.values())
