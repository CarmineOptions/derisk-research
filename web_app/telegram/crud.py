from typing import Sequence
from uuid import UUID

from sqlalchemy import update, select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, create_async_engine

from database.crud import ModelType
from database.models import NotificationData, Base
from telegram.config import DATABASE_URL


def get_async_engine() -> AsyncEngine:
    return create_async_engine(DATABASE_URL)


def get_async_sessionmaker(engine: AsyncEngine = None) -> async_sessionmaker:
    if engine is None:
        engine = get_async_engine()
    return async_sessionmaker(engine)


class TelegramCrud:
    def __init__(self, sessionmaker: async_sessionmaker):
        self.Session = sessionmaker

    async def delete_object(self, model: type[Base] = None, obj_id: UUID | str = None) -> None:
        async with self.Session() as db:
            stmp = delete(NotificationData).where(NotificationData.id == obj_id)
            await db.execute(stmp)
            await db.commit()

    async def delete_objects_by_filter(self, model: type[Base], /, **filters) -> None:
        async with self.Session() as db:
            stmp = delete(NotificationData).filter_by(**filters)
            await db.execute(stmp)
            await db.commit()

    async def update_values(self, model: type[Base], obj_id: UUID | str, /, **values) -> None:
        async with self.Session() as db:
            stmp = update(model).where(model.id == obj_id).values(**values)
            await db.execute(stmp)
            await db.commit()

    async def get_objects_by_filter(self, model: type[ModelType], offset: int, limit: int, /,
                                    **filters) -> Sequence[ModelType] | ModelType | None:
        async with self.Session() as db:
            stmp = select(model).filter_by(**filters).offset(offset).limit(limit)
            if limit == 1:
                return await db.scalar(stmp)
            return await db.scalars(stmp).all()
