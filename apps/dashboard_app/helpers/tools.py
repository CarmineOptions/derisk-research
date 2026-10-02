from __future__ import annotations

import logging
from decimal import Decimal, getcontext
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set decimal precision
getcontext().prec = 78


def calculate_liquidation_price(
    collateral: Decimal,
    debt: Decimal,
    collateral_token_price: Decimal,
    debt_token_price: Decimal,
    pool_fees: Decimal = Decimal("0"),
    collateral_decimals: int = 18,
    debt_decimals: int = 18,
) -> Decimal:
    """Calculate the liquidation price for a position."""
    if collateral == 0 or debt == 0:
        return Decimal("0")

    # Simplified liquidation price calculation
    loan_to_value = (debt / collateral_token_price) / (collateral / debt_token_price)
    liquidation_threshold = Decimal("1") - pool_fees
    liquidation_price = (debt / collateral) * (collateral_token_price / debt_token_price)

    return liquidation_price


def get_position_data_from_contract(
    collateral_token_address: str,
    debt_token_address: str,
) -> list[dict]:
    """Get position data from the contract."""
    # This would typically query on-chain data
    # For now, return mock data structure
    return [
        {
            "user": "0x1234567890abcdef1234567890abcdef12345678",
            "collateral": Decimal("1000000000000000000"),
            "debt": Decimal("500000000000000000"),
        },
    ]


def calc_token_amount(
    raw_amount: Decimal,
    decimals: int,
) -> Decimal:
    """Convert raw token amount to human-readable format."""
    return raw_amount / (Decimal(10) ** decimals)


def format_token_amount(amount: Decimal | str) -> str:
    """Format token amount for display."""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return f"{amount:,.4f}"


def format_usd_value(value: Decimal | str) -> str:
    """Format USD value for display."""
    if isinstance(value, str):
        value = Decimal(value)
    return f"${value:,.2f}"
