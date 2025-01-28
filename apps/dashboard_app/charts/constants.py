from dataclasses import dataclass


@dataclass
class ChartsHeaders:
    low_health_factor_loans: str = "Loans with low health factor"
    top_loans: str = "Top loans"
