import logging
from typing import Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select

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


db_connector = DashboardDBConnectorAsync(SQLALCHEMY_DATABASE_URL)
