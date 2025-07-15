import logging
from typing import Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select, text

from shared.db import Base, DBConnectorAsync, SQLALCHEMY_DATABASE_URL
from ..utils.values import (
    CURRENTLY_AVAILABLE_PROTOCOL_IDS,
    NotificationValidationValues,
)

logger = logging.getLogger(__name__)
ModelType = TypeVar("ModelType", bound=BaseModel)


class DashboardDBConnectorAsync(DBConnectorAsync):
    async def get_all_activated_subscribers(
        self, model: Type[Base] = None
    ) -> ModelType:
        """
        Retrieves all activated subscribers from the database who have valid telegram IDs
        and are subscribed to currently available protocols.

        Args:
            model: Type[Base] - Model class to query for subscribers

        Returns:
            ModelType | None - List of activated subscriber objects or None if no records found
        """
        async with self.session() as db:
            result = await db.execute(
                select(model).where(
                    func.char_length(model.telegram_id)
                    >= NotificationValidationValues.telegram_id_min_length,
                    model.protocol_id.in_(CURRENTLY_AVAILABLE_PROTOCOL_IDS),
                )
            )

            return result.scalars().all()

    async def get_user_debt(self, protocol_id: str, wallet_id: str) -> float | None:
        """
        Fetches user debt for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID.
            wallet_id (str): User's wallet ID.

        Returns:
            float | None: User debt if found, otherwise None.
        """
        async with self.session() as db:
            sql = text("""
                SELECT debt FROM loan_state
                WHERE protocol_id = :protocol_id and "user" = :user;
            """)
            res = await db.execute(sql, {"protocol_id": protocol_id, "user": wallet_id})
            return res.scalar_one_or_none()

    async def get_user_deposit(self, protocol_id: str, wallet_id: str) -> float | None:
        """
        Fetches user deposit for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID.
            wallet_id (str): User's wallet ID.

        Returns:
            float | None: User deposit if found, otherwise None.
        """
        async with self.session() as db:
            sql = text("""
                SELECT deposit FROM loan_state
                WHERE protocol_id = :protocol_id and "user" = :user;
            """)
            res = await db.execute(sql, {"protocol_id": protocol_id, "user": wallet_id})
            return res.scalar_one_or_none()

    async def get_user_collateral(
        self, protocol_id: str, wallet_id: str
    ) -> float | None:
        """
        Fetches user collateral for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID.
            wallet_id (str): User's wallet ID.

        Returns:
            float | None: User collateral if found, otherwise None.
        """
        async with self.session() as db:
            sql = text("""
                SELECT collateral FROM loan_state
                WHERE protocol_id = %s and "user" = %s;
            """)
            res = await db.execute(sql, {"protocol_id": protocol_id, "user": wallet_id})
            return res.scalar_one_or_none()

    async def get_loan_state(self, protocol_id: str, wallet_id: str) -> dict | None:
        """
        Fetches user loan state for a given protocol and wallet.

        Args:
            protocol_id (str): Protocol ID.
            wallet_id (str): User's wallet ID.

        Returns:
            dict | None: User's loan state if found, otherwise None.
        """
        async with self.session() as db:
            sql = text("""
                SELECT collateral, debt, deposit FROM loan_state
                WHERE protocol_id = %s and "user" = %s;
            """)
            res = (
                await db.execute(sql, {"protocol_id": protocol_id, "user": wallet_id})
            ).one()
            return {
                "collateral": res[0],
                "debt": res[1],
                "deposit": res[2],
            }


db_connector = DashboardDBConnectorAsync(SQLALCHEMY_DATABASE_URL)
