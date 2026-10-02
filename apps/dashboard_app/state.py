from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from apps.dashboard_app.config import (
    COLLATERAL_TOKEN_ADDRESS,
    COLLATERAL_TOKEN_DECIMALS,
    COLLATERAL_TOKEN_SYMBOL,
    COLLATERAL_TOKEN_UNDERLYING_ADDRESS,
    DEBT_TOKEN_ADDRESS,
    DEBT_TOKEN_DECIMALS,
    DEBT_TOKEN_SYMBOL,
    DEBT_TOKEN_UNDERLYING_ADDRESS,
)
from apps.dashboard_app.constants import POOL_FEES
from apps.dashboard_app.helpers.tools import (
    get_position_data_from_contract,
    calculate_liquidation_price,
    calc_token_amount,
)
from apps.shared.redis_client import get_redis_client

if TYPE_CHECKING:
    from decimal import Decimal

logger = logging.getLogger(__name__)


class DashboardState:
    def __init__(self) -> None:
        self.collateral_token_address = COLLATERAL_TOKEN_ADDRESS
        self.collateral_token_symbol = COLLATERAL_TOKEN_SYMBOL
        self.collateral_token_decimals = COLLATERAL_TOKEN_DECIMALS
        self.debt_token_address = DEBT_TOKEN_ADDRESS
        self.debt_token_symbol = DEBT_TOKEN_SYMBOL
        self.debt_token_decimals = DEBT_TOKEN_DECIMALS
        self.collateral_token_underlying_address = COLLATERAL_TOKEN_UNDERLYING_ADDRESS
        self.debt_token_underlying_address = DEBT_TOKEN_UNDERLYING_ADDRESS
        self.pool_fees = POOL_FEES
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    async def compute_liquidable_debt_at_price(
        self,
        prices: dict[str, float],
        collateral_token_underlying_address: str,
        collateral_token_price: float,
        debt_token_underlying_address: str,
    ) -> list[dict]:
        """Compute liquidable debt at given prices. This is a long-running operation."""
        positions_data = get_position_data_from_contract(
            self.collateral_token_address,
            self.debt_token_address,
        )

        results = []
        for position in positions_data:
            liquidation_price = calculate_liquidation_price(
                position["collateral"],
                position["debt"],
                collateral_token_price,
                debt_token_price=prices.get(debt_token_underlying_address.lower(), 0),
                pool_fees=self.pool_fees,
                collateral_decimals=self.collateral_token_decimals,
                debt_decimals=self.debt_token_decimals,
            )

            is_liquidable = liquidation_price > collateral_token_price

            results.append(
                {
                    "user": position["user"],
                    "collateral": position["collateral"],
                    "debt": position["debt"],
                    "liquidation_price": str(liquidation_price),
                    "is_liquidable": is_liquidable,
                    "collateral_token_price": str(collateral_token_price),
                }
            )

        return results

    def get_liquidable_debt_from_redis(self) -> list[dict]:
        """Read liquidable debt data from Redis."""
        import orjson as json
        redis_client = self._get_redis()
        data = redis_client.get("liquidable_debt")
        if data:
            return json.loads(data)
        return []

    def get_collateral_price_from_redis(self) -> float:
        """Read collateral token price from Redis."""
        import orjson as json
        redis_client = self._get_redis()
        data = redis_client.get("collateral_token_price")
        if data:
            return float(data)
        return 0.0

    def get_debt_price_from_redis(self) -> float:
        """Read debt token price from Redis."""
        import orjson as json
        redis_client = self._get_redis()
        data = redis_client.get("debt_token_price")
        if data:
            return float(data)
        return 0.0

    def streamlit_dev_fill_with_test_data(self, data: dict) -> None:
        """Fill Redis with test data for development."""
        import orjson as json
        redis_client = self._get_redis()
        for key, value in data.items():
            redis_client.set(key, json.dumps(value) if isinstance(value, (list, dict)) else str(value))


state = DashboardState()
