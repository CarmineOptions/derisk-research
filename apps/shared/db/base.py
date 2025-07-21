import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar

# from data_handler.db.models.loan_states import ZkLendCollateralDebt
from shared.db.conf import SQLALCHEMY_DATABASE_URL
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from re import sub
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import uuid4, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr
from sqlalchemy import Column, MetaData

logger = logging.getLogger(__name__)
ModelType = TypeVar("ModelType", bound=BaseModel)


class Base(DeclarativeBase):
    id: Mapped[UUID] = Column(PG_UUID(as_uuid=True), default=uuid4, primary_key=True)
    metadata = MetaData()

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()


class DBConnectorAsync:
    """
    Provides database connection and operations management using SQLAlchemy
    in a FastAPI application context.

    Methods:
    - write_to_db: Writes an object to the database.
    - get_object: Retrieves an object by its ID in the database.
    - get_objects: Retrieves a list of objects from the database.
    - get_object_by_field: Retrieves an object from the database by a specific field.
    - delete_object_by_id: Deletes an object by its ID from the database.
    - delete_object: Deletes an object from the database.
    """

    # TODO: change db_url fetching logic by implementing a dedicated method
    #  in app.core.config Settings class
    def __init__(self, db_url: str):
        """
        Initializes a new database connection and session factory for async ORM operations.

        Args:
             db_url: str - The database URL used to create the engine.
        """
        self.engine = create_async_engine(db_url)
        self.session_maker = async_sessionmaker(self.engine)
        self.tables_created = False

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_db(self):
        if not self.tables_created:
            await self.create_tables()
            self.tables_created = True
        async with self.session_maker() as session:
            yield session

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Manages a database session using an asynchronous context manager.

        Yields:
            AsyncSession: The database session.

        Raises:
            Exception: If an error occurs while processing the database operation.
        """
        session: AsyncSession = self.session_maker()

        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error occurred while processing database operation: {e}")
            raise Exception("Error occurred while processing database operation") from e
        finally:
            await session.close()

    async def write_to_db(self, obj: ModelType = None) -> ModelType:
        """
        Writes an object to the database.

        Args:
            obj: Base - Object instance to write to the database.

        Returns:
            Base - The object instance after being written to the database.
        """
        try:
            async with self.session() as db:
                obj = await db.merge(obj)
                await db.commit()
                await db.refresh(obj)
                return obj
        except Exception as e:
            logger.info(f"Error{e}")

    async def get_object(
        self, model: Type[ModelType] = None, obj_id: uuid.UUID = None
    ) -> Optional[ModelType]:
        """
        Retrieves an object by its ID from the database.

        Args:
            model: Type[Base] - Model class to query
            obj_id: UUID - Object's unique identifier

        Returns:
            Optional[Base] - Object instance or None if not found
        """
        async with self.session() as db:
            return await db.get(model, obj_id)

    async def get_objects(self, model: Type[ModelType] = None, **kwargs) -> list[ModelType]:
        """
        Retrieves a list of objects from the database.

        Args:
            model: Type[Base] - Model class to query

        Returns:
            list[Base] - List of object instances or an empty list if no records were found
        """
        async with self.session() as db:
            stmt = select(model).filter_by(**kwargs)
            result = await db.execute(stmt)
            return result.scalars().all()

    async def get_object_by_field(
        self, model: Type[ModelType] = None, field: str = None, value: str = None
    ) -> Optional[ModelType]:
        """
        Retrieves an object from the database by a specific field.

        Args:
            model: Type[Base] - Model class to query
            field: str - Field name
            value: str - Field value

        Returns:
            Optional[Base] - Object instance or None if not found
        """
        async with self.session() as db:
            result = await db.execute(select(model).where(getattr(model, field) == value))
            return result.scalar_one_or_none()

    async def delete_object_by_id(self, model: Type[ModelType], obj_id: uuid.UUID) -> None:
        """
        Deletes an object by its ID from the database.
        Uses Idempotent Delete approach.

        Args:
            model: Type[Base] - Model class to query.
            obj_id: UUID - Object's unique identifier.
        """
        async with self.session() as db:
            obj = await db.get(model, obj_id)
            if obj:
                await db.delete(obj)
                await db.commit()

    async def delete_object(self, obj: ModelType) -> None:
        """
        Deletes an existing object from the database.

        Args:
            obj: Base - Object instance to delete.
        """
        async with self.session() as db:
            await db.delete(obj)
            await db.commit()


db_connector = DBConnectorAsync(SQLALCHEMY_DATABASE_URL)
