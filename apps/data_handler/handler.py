from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

import orjson as json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio import ConnectionPool, Redis

from apps.dashboard_app.state import state
from apps.data_handler.config import (
    COLLATERAL_TOKEN_UNDERLYING_ADDRESS,
    CRONTAB_TIME,
    DEBT_TOKEN_UNDERLYING_ADDRESS,
    REDIS_HOST,
    REDIS_PORT,
)
from apps.shared.redis_client import get_redis_pool
from apps.utils.helpers import ONE_MINUTE_IN_MILISECONDS

if TYPE_CHECKING:
    from decimal import Decimal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_KEY_LIQUIDABLE_DEBT = "liquidable_debt"
REDIS_KEY_COLLATERAL_PRICE = "collateral_token_price"
REDIS_KEY_DEBT_PRICE = "debt_token_price"


class DataHandler:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client
        self.scheduler = AsyncIOScheduler()

    async def _compute_and_store_liquidable_debt(self) -> None:
        """Compute liquidable debt at current prices and store in Redis."""
        logger.info("Computing liquidable debt...")
        start_time = time.time()
        try:
            collateral_price_raw = await self._get_or_fetch_price(
                COLLATERAL_TOKEN_UNDERLYING_ADDRESS
            )
            debt_price_raw = await self._get_or_fetch_price(
                DEBT_TOKEN_UNDERLYING_ADDRESS
            )

            collateral_price = float(collateral_price_raw)
            debt_price = float(debt_price_raw)

            prices = {
                COLLATERAL_TOKEN_UNDERLYING_ADDRESS.lower(): collateral_price,
                DEBT_TOKEN_UNDERLYING_ADDRESS.lower(): debt_price,
            }

            liquidable_debt = await state.compute_liquidable_debt_at_price(
                prices=prices,
                collateral_token_underlying_address=COLLATERAL_TOKEN_UNDERLYING_ADDRESS,
                collateral_token_price=collateral_price,
                debt_token_underlying_address=DEBT_TOKEN_UNDERLYING_ADDRESS,
            )

            # Store individual values in Redis
            await self.redis_client.set(
                REDIS_KEY_COLLATERAL_PRICE, str(collateral_price)
            )
            await self.redis_client.set(REDIS_KEY_DEBT_PRICE, str(debt_price))
            await self.redis_client.set(
                REDIS_KEY_LIQUIDABLE_DEBT, json.dumps(liquidable_debt)
            )

            elapsed = time.time() - start_time
            logger.info(
                f"Computed and stored liquidable debt in {elapsed:.2f}s"
            )
        except Exception as e:
            logger.error(f"Error computing liquidable debt: {e}")

    async def _get_or_fetch_price(self, token_address: str) -> Decimal:
        """Get token price from cache or fetch from API."""
        cached = await self.redis_client.get(f"token_price_{token_address.lower()}")
        if cached:
            return Decimal(cached)
        # Fetch from external source
        from apps.shared.price_fetcher import get_token_price
        price = await get_token_price(token_address)
        if price:
            await self.redis_client.set(
                f"token_price_{token_address.lower()}", str(price)
            )
        return price

    async def start(self) -> None:
        """Start the data handler."""
        logger.info("Starting DataHandler...")
        self.scheduler.add_job(
            self._compute_and_store_liquidable_debt,
            "interval",
            seconds=CRONTAB_TIME * 60,
            id="liquidable_debt_computation",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info(
            f"DataHandler started. Interval: {CRONTAB_TIME} minutes."
        )
        # Run initial computation
        await self._compute_and_store_liquidable_debt()
        # Keep the event loop running
        while True:
            await asyncio.sleep(1)


async def main() -> None:
    pool = get_redis_pool()
    redis_client = Redis(connection_pool=pool)
    handler = DataHandler(redis_client)
    await handler.start()


if __name__ == "__main__":
    asyncio.run(main())
