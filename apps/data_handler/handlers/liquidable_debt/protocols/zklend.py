```python
"""
ZkLend liquidation protocol handler
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from src.app.base.protocol.protocol_handler_base import (
    ProtocolHandlerBase,
    ProtocolLiquidityPosition,
)
from src.infrastructure.blockchain_client.contracts.zklend.markets_provider_contract import (
    MarketsProviderContract,
)
from src.infrastructure.blockchain_client.contracts.zklend.zklend_ERC20_token_contract import (
    ZkLendERCTokenContract,
)
from src.infrastructure.config_manager.config import ConfigManager
from src.infrastructure.utils import to_timestamp
from src.domain.entities.asset import Asset
from src.domain.entities.block import Block
from src.domain.enums import ChainType

logger = logging.getLogger(__name__)


@dataclass
class ZkLendProtocolHandler(ProtocolHandlerBase):
    """
    ZkLend Protocol Handler
    """

    MAX_CONCURRENT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    MIN_HEALTH_FACTOR: Decimal = Decimal("0.95")

    _markets_provider_contract: MarketsProviderContract = field(
        init=False, repr=False
    )
    _rate_limit_semaphore: asyncio.Semaphore = field(init=False, repr=False)
    _last_request_timestamps: list = field(default_factory=list, init=False, repr=False)

    async def initialize(self) -> None:
        super().initialize()
        self._rate_limit_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

    def _get_client_address(self, config: ConfigManager) -> str:
        return config.get_value(f"contracts.zklend.{ChainType.STARKNET.name.lower()}")

    def _get_markets_contract_address(self, config: ConfigManager) -> str:
        return config.get_value(
            f"contracts.zklend_markets.{ChainType.STARKNET.name.lower()}"
        )

    async def _fetch_market_data_with_rate_limit(
        self, contract: ZkLendERCTokenContract, asset: Asset
    ) -> dict:
        """Fetch market data with rate limiting applied."""

        async with self._rate_limit_semaphore:
            self._enforce_rate_limit()
            try:
                return await contract.fetch_market_data(asset)
            except Exception as e:
                logger.error(
                    f"Failed to fetch market data for {asset.symbol}: {e}"
                )
                return {}
            finally:
                self._record_request_timestamp()

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limit by waiting if necessary."""
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.RATE_LIMIT_WINDOW_SECONDS

        # Remove timestamps outside the window
        self._last_request_timestamps = [
            ts for ts in self._last_request_timestamps if ts > window_start
        ]

        # If we've hit the limit, wait until the oldest request falls out of the window
        if len(self._last_request_timestamps) >= self.MAX_CONCURRENT_REQUESTS:
            wait_time = self._last_request_timestamps[0] - window_start + 0.1
            if wait_time > 0:
                logger.debug(
                    f"Rate limit reached, waiting {wait_time:.2f}s before next request"
                )
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: asyncio.sleep(wait_time)
                )

    def _record_request_timestamp(self) -> None:
        """Record the timestamp of a request."""
        self._last_request_timestamps.append(datetime.now(timezone.utc).timestamp())

    async def get_liquidatable_positions(
        self, assets: list[Asset], block: Block
    ) -> list[ProtocolLiquidityPosition]:
        """
        Fetch liquidation positions from ZkLend protocol.

        Args:
            assets: List of Asset objects to check
            block: Block object to query at

        Returns:
            List of liquidatable positions
        """
        positions: list[ProtocolLiquidityPosition] = []

        if not self._markets_provider_contract:
            self._markets_provider_contract = MarketsProviderContract(
                self.client, self._get_markets_contract_address(self.config)
            )

        markets_data = await self._markets_provider_contract.get_all_markets_data()

        # Filter assets that exist in ZkLend markets and are liquidatable
        for asset in assets:
            if not asset.address or asset.address not in markets_data:
                logger.debug(
                    f"Asset {asset.symbol} not found in ZkLend markets, skipping"
                )
                continue

            # Fetch market data with rate limiting
            market_data = await self._fetch_market_data_with_rate_limit(
                self._get_token_contract(asset), asset
            )

            if not market_data:
                continue

            # Check if position is liquidatable
            if self._is_liquidatable(market_data):
                position = self._create_liquidation_position(
                    asset, market_data, block
                )
                if position:
                    positions.append(position)

        return positions

    def _get_token_contract(self, asset: Asset) -> ZkLendERCTokenContract:
        """Get token contract for an asset."""
        return ZkLendERCTokenContract(self.client, asset.address)

    def _is_liquidatable(self, market_data: dict) -> bool:
        """Check if the market data indicates a liquidatable position."""
        try:
            health_factor = market_data.get("health_factor", Decimal("1"))
            return health_factor < self.MIN_HEALTH_FACTOR
        except Exception as e:
            logger.error(f"Error checking liquidation status: {e}")
            return False

    def _create_liquidation_position(
        self, asset: Asset, market_data: dict, block: Block
    ) -> ProtocolLiquidityPosition | None:
        """Create a liquidation position from market data."""
        try:
            return ProtocolLiquidityPosition(
                id=f"zklend_{asset.symbol}_{block.number}",
                protocol="zkLend",
                chain=ChainType.STARKNET,
                asset=asset,
                block_number=block.number,
                timestamp=to_timestamp(block.timestamp),
                liquidation_price=market_data.get("price", Decimal("0")),
                health_factor=market_data.get("health_factor", Decimal("1")),
                collateral_amount=market_data.get("total_collateral", Decimal("0")),
                debt_amount=market_data.get("total_debt", Decimal("0")),
                extra_data={"token_symbol": asset.symbol},
            )
        except Exception as e:
            logger.error(f"Error creating liquidation position: {e}")
            return None
