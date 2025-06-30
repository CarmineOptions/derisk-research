import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar

from data_handler.db.models.loan_states import ZkLendCollateralDebt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)
ModelType = TypeVar("ModelType", bound=BaseModel)


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
        async with self.session() as db:
            obj = await db.merge(obj)
            await db.commit()
            await db.refresh(obj)
            return obj

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

    async def get_objects(
        self, model: Type[ModelType] = None, **kwargs
    ) -> list[ModelType]:
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
            result = await db.execute(
                select(model).where(getattr(model, field) == value)
            )
            return result.scalar_one_or_none()

    async def delete_object_by_id(
        self, model: Type[ModelType], obj_id: uuid.UUID
    ) -> None:
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


class InitializerDBConnectorAsync:
    """
    Provides asynchronous database connection and CRUD operations for ZkLendCollateralDebt.

    Methods:
    - get_zklend_by_user_ids: Retrieves ZkLendCollateralDebt records by user_ids.
    - save_collateral_enabled_by_user: Updates or creates a ZkLendCollateralDebt record.
    """

    def __init__(self, db_url: str):
        """
        Initialize the async database connection and session factory.

        Args:
            db_url: Database connection URL.
        """
        self.engine = create_async_engine(db_url)
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Async context manager for database sessions."""
        async with self.session_factory() as session:
            try:
                yield session
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                await session.close()

    async def get_zklend_by_user_ids(
        self, user_ids: List[str]
    ) -> List[ZkLendCollateralDebt]:
        """
        Retrieves ZkLendCollateralDebt records by user_ids.

        Args:
            user_ids: List of user IDs to query

        Returns:
            List of ZkLendCollateralDebt objects
        """
        async with self.session() as session:
            result = await session.execute(
                select(ZkLendCollateralDebt).where(
                    ZkLendCollateralDebt.user_id.in_(user_ids)
                )
            )
            return result.scalars().all()

    @staticmethod
    def _convert_decimal_to_float(
        data: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """
        Convert Decimal values to float for JSON serialization.

        Args:
            data: Dictionary potentially containing Decimal values

        Returns:
            Dictionary with Decimal values converted to float or None
        """
        if data:
            return {
                k: float(v) if isinstance(v, Decimal) else v for k, v in data.items()
            }
        return None

    async def save_collateral_enabled_by_user(
        self,
        user_id: str,
        collateral_enabled: Dict[str, bool],
        collateral: Optional[Dict[str, Any]] = None,
        debt: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Updates or creates a ZkLendCollateralDebt record.

        Args:
            user_id: User ID to update/create
            collateral_enabled: Collateral enabled status dictionary
            collateral: Optional collateral data
            debt: Optional debt data
        """
        processed_collateral = self._convert_decimal_to_float(collateral)
        processed_debt = self._convert_decimal_to_float(debt)

        async with self.session() as session:
            result = await session.execute(
                select(ZkLendCollateralDebt).where(
                    ZkLendCollateralDebt.user_id == user_id
                )
            )
            record = result.scalar_one_or_none()

            if record:
                if processed_collateral is not None:
                    record.collateral = processed_collateral
                if processed_debt is not None:
                    record.debt = processed_debt
                record.collateral_enabled = collateral_enabled
            else:
                new_record = ZkLendCollateralDebt(
                    user_id=user_id,
                    collateral=processed_collateral if processed_collateral else {},
                    debt=processed_debt if processed_debt else {},
                    deposit={},
                    collateral_enabled=collateral_enabled,
                )
                session.add(new_record)
            await session.commit()
