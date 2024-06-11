import uuid
from typing import List, Optional, Type, TypeVar

from sqlalchemy import create_engine, func, select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker, Session, aliased

from db.database import SQLALCHEMY_DATABASE_URL
from db.models import Base, LoanState, InterestRate, OrderBookModel
from handler_tools.constants import ProtocolIDs


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
        :param objects: List[Base] - A list of Base instances to write.
        :raise SQLAlchemyError: If the database operation fails.
        """
        db: Session = self.Session()
        try:
            db.bulk_save_objects(objects)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def write_loan_states_to_db(self, objects: List[LoanState]) -> None:
        """
        Writes a batch of objects to the database efficiently.
        :param objects: List[LoanState] - A list of LoanState instances to write.
        :raise SQLAlchemyError: If the database operation fails.
        """
        db: Session = self.Session()
        try:
            # Fetch existing objects from the database based on protocol_id and user pair
            existing_objects = {
                (obj.protocol_id, obj.user): obj
                for obj in db.execute(
                    select(LoanState).where(
                        (LoanState.protocol_id.in_([o.protocol_id for o in objects]))
                        & (LoanState.user.in_([o.user for o in objects]))
                    )
                ).scalars()
            }

            # Prepare list of objects to save
            objects_to_save = []
            for obj in objects:
                existing_obj = existing_objects.get((obj.protocol_id, obj.user))
                if existing_obj:
                    if (
                        obj.user != existing_obj.user
                        or obj.collateral != existing_obj.collateral
                        or obj.debt != existing_obj.debt
                        or obj.protocol_id != existing_obj.protocol_id
                    ):
                        objects_to_save.append(obj)
                else:
                    objects_to_save.append(obj)

            # Save the filtered objects
            if objects_to_save:
                db.bulk_save_objects(objects_to_save)
                db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_latest_order_book(self, dex: str, token_a: str, token_b: str) -> OrderBookModel | None:
        """
        Retrieves the latest order book for a given pair of tokens and DEX.
        :param dex: str - The DEX name.
        :param token_a: str - The base token address.
        :param token_b: str - The quote token address.
        :return: OrderBookModel instance or None.
        """
        db = self.Session()
        try:
            order_book_condition = and_(
                OrderBookModel.dex == dex,
                OrderBookModel.token_a == token_a,
                OrderBookModel.token_b == token_b,
            )
            max_timestamp = (
                select(func.max(OrderBookModel.timestamp))
                .where(order_book_condition).
                scalar_subquery()
            )
            return db.execute(
                select(OrderBookModel).where(
                    OrderBookModel.timestamp == max_timestamp,
                    order_book_condition
                )
            ).scalar()
        finally:
            db.close()

    def get_unique_users_last_block_objects(
        self, protocol_id: ProtocolIDs
    ) -> LoanState:
        """
        Retrieves the latest loan states for unique users.
        """
        db = self.Session()
        try:
            # Create a subquery to get the max block for each user
            subquery = (
                db.query(LoanState.user, func.max(LoanState.block).label("max_block"))
                .filter(LoanState.protocol_id == protocol_id)
                .group_by(LoanState.user)
                .subquery()
            )

            # Alias the subquery for clarity
            alias_subquery = aliased(subquery)

            # Join the main LoanState table with the subquery
            return (
                db.query(LoanState)
                .join(
                    alias_subquery,
                    and_(
                        LoanState.user == alias_subquery.c.user,
                        LoanState.block == alias_subquery.c.max_block,
                    ),
                )
                .filter(LoanState.protocol_id == protocol_id)
                .all()
            )
        finally:
            db.close()

    def get_last_interest_rate_record_by_protocol_id(
        self, protocol_id: ProtocolIDs
    ) -> InterestRate:
        """
        Retrieves the last interest rate record by protocol ID.
        :param protocol_id: ProtocolIDs - The protocol ID to filter by.
        :return: InterestRate | None
        """
        db = self.Session()
        try:
            return (
                db.query(InterestRate)
                .filter(InterestRate.protocol_id == protocol_id)
                .order_by(InterestRate.block.desc())
                .first()
            )
        finally:
            db.close()
