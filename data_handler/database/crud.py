import uuid
import pandas as pd
from typing import List, Optional, Type, TypeVar

from sqlalchemy import create_engine, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker

from database.database import SQLALCHEMY_DATABASE_URL
from database.models import Base, LoanState
from tools.constants import ProtocolIDs

ModelType = TypeVar("ModelType", bound=Base)


class DBConnector:
    """
    Provides database connection and operations management using SQLAlchemy
    in a FastAPI application context.

    Methods:
    - write_to_db: Writes an object to the database.
    - get_object: Retrieves an object by its ID in the database.
    - remove_object: Removes an object by its ID from the database.
    """

    def __init__(self, db_url: str = SQLALCHEMY_DATABASE_URL):
        """
        Initialize the database connection and session factory.
        :param db_url: str = None
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def write_to_db(self, obj: Base = None) -> None:
        """
        Writes an object to the database. Rolls back transaction if there's an error.
        :param obj: Base = None
        :raise SQLAlchemyError: If the database operation fails.
        :return: None
        """
        db = self.Session()
        try:
            db.add(obj)
            db.commit()

        except SQLAlchemyError as e:
            db.rollback()
            raise e

        finally:
            db.close()

    def get_object(
        self, model: Type[ModelType] = None, obj_id: uuid = None
    ) -> ModelType | None:
        """
        Retrieves an object by its ID from the database.
        :param: model: type[Base] = None
        :param: obj_id: uuid = None
        :return: Base | None
        """
        db = self.Session()
        try:
            return db.query(model).filter(model.id == obj_id).first()
        finally:
            db.close()

    def delete_object(self, model: Type[Base] = None, obj_id: uuid = None) -> None:
        """
        Delete an object by its ID from the database. Rolls back if the operation fails.
        :param model: type[Base] = None
        :param obj_id: uuid = None
        :return: None
        :raise SQLAlchemyError: If the database operation fails
        """
        db = self.Session()

        try:
            obj = db.query(model).filter(model.id == obj_id).first()
            if obj:
                db.delete(obj)
                db.commit()

            db.rollback()

        except SQLAlchemyError as e:
            db.rollback()
            raise e

        finally:
            db.close()

    def get_loans(
        self,
        model: Type[Base],
        protocol: Optional[str] = None,
        user: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        start_datetime: Optional[int] = None,
        end_datetime: Optional[int] = None,
    ):
        """
        Retrieves loans based on various search criteria.
        """
        db = self.Session()
        try:
            query = db.query(model)
            if protocol:
                query = query.filter(model.protocol == protocol)
            if user:
                query = query.filter(model.user == user)
            if start_block is not None:
                query = query.filter(model.block >= start_block)
            if end_block is not None:
                query = query.filter(model.block <= end_block)
            if start_datetime is not None:
                query = query.filter(model.timestamp >= start_datetime)
            if end_datetime is not None:
                query = query.filter(model.timestamp <= end_datetime)

            return query.all()
        finally:
            db.close()

    def get_last_block(self, protocol_id: ProtocolIDs) -> int:
        """
        Retrieves the last (highest) block number from the database filtered by protocol_id.

        :param protocol_id: ProtocolIDs - The protocol ID to filter by.
        :return: The highest block number as an integer. Returns 0 if no blocks are found.
        """
        db = self.Session()
        try:
            max_block = (
                db.query(func.max(LoanState.block))
                .filter(LoanState.protocol_id == protocol_id)
                .scalar()
            )
            return max_block or 0
        finally:
            db.close()

    def write_batch_to_db(self, objects: List[Base]) -> None:
        """
        Writes a batch of objects to the database efficiently.
        :param objects: List[Base] - A list of SQLAlchemy Base instances to write.
        :raise SQLAlchemyError: If the database operation fails.
        """
        db = self.Session()
        try:
            db.bulk_save_objects(objects)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_existed_records(
        self, model: Type[Base], users: list[str], protocol_id: ProtocolIDs
    ) -> List[dict]:
        """
        Retrieves the existed records from the database filtered by protocol_id, blocks and user
        :param model: Type[Base] - The model to filter by.
        :param users: list[str] - The list of users to filter by.
        :param protocol_id: ProtocolIDs - The protocol ID to filter by.
        :return: List[dict] - A list of dictionaries representing the existing records.
        """
        db = self.Session()
        try:
            result = (
                db.query(model)
                .filter(model.protocol_id == protocol_id, model.user.in_(users))
                .all()
            )
            # Convert the list of SQLAlchemy objects to a list of dictionaries
            result_df = pd.DataFrame([record.__dict__ for record in result])
            # Remove the '_sa_instance_state' key which is not needed
            clear_df = result_df.drop("_sa_instance_state", axis=1, errors="ignore")
            return clear_df
        finally:
            db.close()
