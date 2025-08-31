from dataclasses import dataclass
from enum import Enum

SUPPLY_STATS_TOKEN_SYMBOLS_MAPPING = {
    "eth": "ETH",
    "wbtc": "WBTC",
    "usdc": "USDC",
    "usdt": "USDT",
    "wsteth": "wstETH",
    "lords": "LORDS",
    "strk": "STRK",
    "kstrk": "kSTRK",
}


@dataclass
class ChartsHeaders:
    low_health_factor_loans: str = "Loans with low health factor"
    top_loans: str = "Top loans"
    detail_loans: str = "Detail of a loan"
    comparison_lending_protocols: str = "Comparison of lending protocols"


class CommonValues(Enum):
    amount_usd = "amount_usd"
    token = "token"
    debt_usd = "Debt (USD)"
    collateral_usd = "Collateral (USD)"
    user = "User"
    protocol = "Protocol"
    health_factor = "Health factor"
    standardized_health_factor = "Standardized health factor"
