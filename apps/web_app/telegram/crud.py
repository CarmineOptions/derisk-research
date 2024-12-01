from typing import Sequence
from uuid import UUID

from database.crud import ModelType
from database.models import Base, NotificationData
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from telegram.config import DATABASE_URL


def get_async_engine() -> AsyncEngine:
    """
    Get an asynchronous SQLAlchemy engine instance using the configured DATABASE_URL.

    Returns:
       AsyncEngine: An asynchronous SQLAlchemy engine instance.
    """
    return create_async_engine(DATABASE_URL)


def get_async_sessionmaker(engine: AsyncEngine = None) -> async_sessionmaker:
    """
    Get an asynchronous SQLAlchemy session maker instance.

    Args:
        engine (AsyncEngine, optional): An asynchronous SQLAlchemy engine instance.
            If not provided, it will use the engine from `get_async_engine()`.

    Returns:
        async_sessionmaker: An asynchronous SQLAlchemy session maker instance.
    """
    if engine is None:
        engine = get_async_engine()
    return async_sessionmaker(engine)


class TelegramCrud:
    def __init__(self, sessionmaker: async_sessionmaker):
        """
        Initialize a TelegramCrud instance with an asynchronous SQLAlchemy session maker.
        Args:
            sessionmaker (async_sessionmaker): An asynchronous SQLAlchemy session maker instance.
        """
        self.Session = sessionmaker

    async def delete_object(
        self, model: type[Base] = None, obj_id: UUID | str = None
    ) -> None:
        """
        Delete an object from the database based on its ID.

        Args:
            model (type[Base], optional): The SQLAlchemy model class for the object to be deleted.
            obj_id (UUID | str, optional): The ID of the object to be deleted.
        """
        async with self.Session() as db:
            stmp = delete(NotificationData).where(NotificationData.id == obj_id)
            await db.execute(stmp)
            await db.commit()

    async def delete_objects_by_filter(self, model: type[Base], /, **filters) -> None:
        """
        Delete objects from the database based on a filter.

        Args:
            model (type[Base]): The SQLAlchemy model class for the objects to be deleted.
            **filters: Key-value pairs representing the filter conditions.
        """
        async with self.Session() as db:
            stmp = delete(NotificationData).filter_by(**filters)
            await db.execute(stmp)
            await db.commit()

    async def update_values(
        self, model: type[Base], obj_id: UUID | str, /, **values
    ) -> None:
        """
        Update values of an object in the database based on its ID.

        Args:
            model (type[Base]): The SQLAlchemy model class for the object to be updated.
            obj_id (UUID | str): The ID of the object to be updated.
            **values: Key-value pairs representing the values to be updated.
        """
        async with self.Session() as db:
            stmp = update(model).where(model.id == obj_id).values(**values)
            await db.execute(stmp)
            await db.commit()

    async def get_objects_by_filter(
        self, model: type[ModelType], offset: int, limit: int, /, **filters
    ) -> Sequence[ModelType] | ModelType | None:
        """
        Get objects from the database based on a filter, with offset and limit.

        Args:
            model (type[ModelType]): The SQLAlchemy model class for the objects to be retrieved.
            offset (int): The offset for the query results.
            limit (int): The maximum number of results to be returned.
            **filters: Key-value pairs representing the filter conditions.

        Returns:
            Sequence[ModelType] | ModelType | None: A sequence of model instances if `limit` is greater than 1,
                a single model instance if `limit` is 1, or None if no objects match the filter.
        """
        async with self.Session() as db:
            stmp = select(model).filter_by(**filters).offset(offset).limit(limit)
            if limit == 1:
                return await db.scalar(stmp)
            return await db.scalars(stmp).all()

    async def write_to_db(self, obj: ModelType) -> None:
        """
        Write an object to the database.

        Args:
            obj (ModelType): The object to be added to the database.
        """
        async with self.Session() as db:
            db.add(obj)
            await db.commit()
