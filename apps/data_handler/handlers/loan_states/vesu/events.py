"""
Module to handle VesuLoan events and calculate health factors.
This module interacts with the VesuLoan contract on Starknet to fetch user positions,
calculate collateral and debt values, and determine health factors for users.
"""

from decimal import Decimal

from shared.starknet_client import StarknetClient
from starknet_py.hash.selector import get_selector_from_name
from data_handler.db.models.liquidable_debt import HealthRatioLevel


class VesuLoanEntity:
    """
    Class to handle VesuLoan events and calculate health factors.
    This class interacts with the VesuLoan contract on Starknet to fetch user positions,
    calculate collateral and debt values, and determine health factors for users.
    It uses a mock database to store user positions and a cache to optimize data retrieval.
    """

    VESU_ADDRESS = "0x02545b2e5d519fc230e9cd781046d3a64e092114f07e44771e0d719d148725ef"

    def __init__(self):
        """Initialize Starknet client and storage."""
        self.client = StarknetClient()
        self.mock_db = {}
        self._cache = {}
        self.last_processed_block = 654244  # First VESU event block

    async def _get_token_decimals(self, token_address: int) -> Decimal:
        """
        Fetch decimals directly from the token contract

        :param token_address: Token address in decimal format

        :return: Decimal factor based on token decimals (10^n)
        """
        result = await self.client.func_call(token_address, "decimals", [])
        if result and len(result) > 0:
            print(f"Decimals for token {hex(token_address)}: {result[0]}")
            decimals = result[0]
            return Decimal(10) ** Decimal(decimals)
        return Decimal("Inf")
    
    async def save_health_ratio_level(
        self, session, timestamp, user_id, value, protocol_id
    ):
        """Save a HealthRatioLevel record to the DB."""
        record = HealthRatioLevel(
            timestamp=timestamp,
            user_id=user_id,
            value=value,
            protocol_id=protocol_id,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def calculate_health_factor(self, user_address: int, session=None) -> dict:
        """
        Calculate health factors for all positions of a user.

        :param user_address: User address in int format

        :return: Dictionary with pool IDs as keys and health factors as values
        """

        user_positions = {k: v for k, v in self.mock_db.items() if k[0] == user_address}

        if not user_positions:
            return {}

        results = {}
        for (_, pool_id), position_data in user_positions.items():
            collateral_asset = position_data["collateral_asset"]
            debt_asset = position_data["debt_asset"]

            if collateral_asset == 0 or debt_asset == 0:
                results[hex(pool_id)] = Decimal("inf")
                continue

            position = await self._get_position_data(
                user_address, pool_id, collateral_asset, debt_asset
            )
            collateral_shares_low, collateral_shares_high = position[0], position[1]
            collateral_sign = 0 if collateral_shares_low >= 0 else 1

            collateral_value = await self._get_collateral_value(
                pool_id,
                collateral_asset,
                collateral_shares_low,
                collateral_shares_high,
                collateral_sign,
            )

            debt_config = await self._get_asset_config(pool_id, debt_asset)
            nominal_debt_low, nominal_debt_high = position[2], position[3]
            debt_sign = 0 if nominal_debt_low >= 0 else 1

            rate_acc_low, rate_acc_high = debt_config[14], debt_config[15]
            scale_low, scale_high = debt_config[10], debt_config[11]

            debt_value = await self._calculate_debt(
                nominal_debt_low,
                nominal_debt_high,
                debt_sign,
                rate_acc_low,
                rate_acc_high,
                scale_low,
                scale_high,
            )

            ltv_data = await self.get_ltv_config(pool_id, collateral_asset, debt_asset)

            collateral_decimals = await self._get_token_decimals(collateral_asset)
            debt_decimals = await self._get_token_decimals(debt_asset)

            collateral_factor = Decimal(ltv_data[0]) / collateral_decimals

            collateral_price = await self.fetch_token_price(collateral_asset, pool_id)
            debt_price = await self.fetch_token_price(debt_asset, pool_id)

            collateral_normalized = collateral_value / collateral_decimals
            debt_normalized = debt_value / debt_decimals

            collateral_usd = collateral_normalized * collateral_price
            debt_usd = debt_normalized * debt_price

            health_factor = (
                (collateral_usd * collateral_factor) / debt_usd
                if debt_usd > 0
                else Decimal("inf")
            )

            results[hex(pool_id)] = health_factor

            if session is not None:
                await self.save_health_ratio_level(
                    session=session,
                    timestamp=position_data.get("block_number", 0),
                    user_id=str(user_address),
                    value=health_factor,
                    protocol_id=pool_id,
                )

        return results

    async def _get_position_data(
        self, user, pool_id, collateral_asset, debt_asset
    ) -> tuple:
        """
        Get user position data with caching.
        :param user: User address in decimal format
        :param pool_id: Pool ID in decimal
        :param collateral_asset: Collateral asset address in decimal format
        :param debt_asset: Debt asset address in decimal format
        :return: Position data as a tuple
        """
        vesu_addr = int(self.VESU_ADDRESS, 16)

        cache_key = f"position_{user}_{pool_id}_{collateral_asset}_{debt_asset}"
        return await self._get_contract_data(
            cache_key,
            self.client.func_call,
            [vesu_addr, "position", [pool_id, collateral_asset, debt_asset, user]],
        )

    async def _get_contract_data(self, cache_key, func, params) -> tuple:
        """
        Get data from contract with caching.

        :param cache_key: Cache key for the data
        :param func: Function to call
        :param params: Parameters for the function call
        :return: Result of the function call
        """
        if cache_key not in self._cache:
            self._cache[cache_key] = await func(*params)
        return self._cache[cache_key]

    async def _get_collateral_value(
        self, pool_id, asset, shares_low, shares_high, sign=0
    ) -> Decimal:
        """
        Calculate collateral value.

        :param pool_id: Pool ID in decimal
        :param asset: Asset address in decimal format
        :param shares_low: Low part of shares
        :param shares_high: High part of shares
        :param sign: Sign of the shares (0 or 1)
        :return: Collateral value as a Decimal
        """
        vesu_addr = int(self.VESU_ADDRESS, 16)

        cache_key = f"collateral_{asset}_{shares_low}_{shares_high}_{sign}"
        result = await self._get_contract_data(
            cache_key,
            self.client.func_call,
            [
                vesu_addr,
                "calculate_collateral",
                [pool_id, asset, shares_low, shares_high, sign],
            ],
        )
        return self._u256_to_decimal(result[0], result[1])

    async def _calculate_debt(
        self,
        nominal_debt_low,
        nominal_debt_high,
        sign,
        rate_accumulator_low,
        rate_accumulator_high,
        scale_low,
        scale_high,
    ) -> Decimal:
        """
        Calculate debt value.

        :param nominal_debt_low: Low part of nominal debt
        :param nominal_debt_high: High part of nominal debt
        :param sign: Sign of the debt (0 or 1)
        :param rate_accumulator_low: Low part of rate accumulator
        :param rate_accumulator_high: High part of rate accumulator
        :param scale_low: Low part of scale
        :param scale_high: High part of scale
        :return: Debt value as a Decimal
        """
        vesu_addr = int(self.VESU_ADDRESS, 16)

        cache_key = f"debt_{nominal_debt_low}_{nominal_debt_high}_{sign}_ \
        {rate_accumulator_low}_{rate_accumulator_high}"
        result = await self._get_contract_data(
            cache_key,
            self.client.func_call,
            [
                vesu_addr,
                "calculate_debt",
                [
                    nominal_debt_low,
                    nominal_debt_high,
                    sign,
                    rate_accumulator_low,
                    rate_accumulator_high,
                    scale_low,
                    scale_high,
                ],
            ],
        )
        return self._u256_to_decimal(result[0], result[1])

    async def _get_asset_config(self, pool_id, asset_address) -> tuple:
        """
        Get asset configuration with caching.

        :param pool_id: Pool ID in decimal
        :param asset_address: Asset address in decimal format
        :return: Asset configuration as a tuple
        """
        vesu_addr = int(self.VESU_ADDRESS, 16)

        cache_key = f"asset_config_{pool_id}_{asset_address}"
        return await self._get_contract_data(
            cache_key,
            self.client.func_call,
            [vesu_addr, "asset_config", [pool_id, asset_address]],
        )

    async def get_ltv_config(self, pool_id, collateral, debt) -> tuple:
        """
        Get LTV configuration with caching.

        :param pool_id: Pool ID in decimal
        :param collateral: Collateral asset address in decimal format
        :param debt: Debt asset address in decimal format
        :return: LTV configuration as a tuple
        """
        vesu_addr = int(self.VESU_ADDRESS, 16)

        cache_key = f"ltv_{pool_id}_{collateral}_{debt}"
        return await self._get_contract_data(
            cache_key,
            self.client.func_call,
            [vesu_addr, "ltv_config", [pool_id, collateral, debt]],
        )

    async def fetch_token_price(self, address, pool_id) -> Decimal:
        """
        Fetch token price using price extension.

        :param address: Token address in decimal format
        :param pool_id: Pool ID in decimal
        :return: Token price as a Decimal
        """
        try:
            vesu_addr = int(self.VESU_ADDRESS, 16)

            cache_key = f"extension_price_{pool_id}"
            if cache_key not in self._cache:
                extension_result = await self.client.func_call(
                    vesu_addr, "extension", [pool_id]
                )
                self._cache[cache_key] = extension_result[0]
            price_extension_addr = self._cache[cache_key]

            price_result = await self.client.func_call(
                price_extension_addr, "price", [pool_id, address]
            )
            price_u256 = price_result[0]
            is_valid = price_result[2] if len(price_result) > 2 else 1

            if not is_valid:
                print(
                    f"Warning: Price for \
                    {address} is not valid"
                )
                return Decimal("1")

            return Decimal(price_u256) / Decimal(10**18)

        except Exception as e:
            print(f"Error fetching price for {address}: {e}")
            return Decimal("1")

    def _u256_to_decimal(self, low, high) -> Decimal:
        """
        Convert u256 (low, high) pair to Decimal.

        :param low: Low part of u256
        :param high: High part of u256

        :return: Decimal representation of u256
        """
        return Decimal(low) + (Decimal(high) * Decimal(2**128))

    async def update_positions_data(self) -> None:
        """
        Process ModifyPosition events to track user positions.
        Uses continuation tokens to fetch all events across multiple pages.

        :return: None
        """
        current_block = await self.client.client.get_block_number()

        if current_block <= self.last_processed_block:
            return

        continuation_token = None
        all_events = []

        while True:
            events = await self.client.client.get_events(
                address=self.VESU_ADDRESS,
                from_block_number=self.last_processed_block + 1,
                to_block_number=current_block,
                keys=[[hex(get_selector_from_name("ModifyPosition"))]],
                chunk_size=5,
                continuation_token=continuation_token,
            )

            all_events.extend(events.events)

            continuation_token = events.continuation_token
            if not continuation_token:
                break

        for event in all_events:
            event_keys = event.keys

            pool_id = event_keys[1]
            collateral_asset = event_keys[2]
            debt_asset = event_keys[3]
            user = event_keys[4]
            block_number = event.block_number

            self.mock_db[(user, pool_id)] = {
                "pool_id": pool_id,
                "collateral_asset": collateral_asset,
                "debt_asset": debt_asset,
                "block_number": block_number,
            }
            self.last_processed_block = max(self.last_processed_block, block_number)
