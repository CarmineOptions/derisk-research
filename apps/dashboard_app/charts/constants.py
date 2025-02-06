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
    amount_usd: str = "amount_usd"
    token: str = "token"
    debt_usd: str = "Debt (USD)"
    collateral_usd: str = "Collateral (USD)"
    user: str = "User"
    protocol: str = "Protocol"
    health_factor: str = "Health factor"
    standardized_health_factor: str = "Standardized health factor"
