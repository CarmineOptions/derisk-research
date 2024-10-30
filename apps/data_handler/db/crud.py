import logging
import uuid
from typing import List, Optional, Type, TypeVar

from data_handler.db.database import SQLALCHEMY_DATABASE_URL
from shared.constants import ProtocolIDs
from sqlalchemy import Subquery, and_, create_engine, desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, aliased, scoped_session, sessionmaker

from data_handler.db.models import (
    Base,
    HashtackCollateralDebt,
    InterestRate,
    LoanState,
    OrderBookModel,
    ZkLendCollateralDebt,
)

from data_handler.db.models.zklend_events import (
    AccumulatorsSyncEventData,
    LiquidationEventData,
)


logger = logging.getLogger(__name__)
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
        
        :param db_url: The database URL to connect to.
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def write_to_db(self, obj: Base = None) -> None:
        """
        Writes an object to the database. Rolls back transaction if there's an error.
        
        :param obj: The database model object to write.
        :raise SQLAlchemyError: If the database operation fails.
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
    ) -> Optional[ModelType]:
        """
        Retrieves an object by its ID from the database.
        
        :param model: The model type to query.
        :param obj_id: The unique ID of the object to retrieve.
        :return: The object found or None.
        """
        db = self.Session()
        try:
            return db.query(model).filter(model.id == obj_id).first()
        finally:
            db.close()

    def delete_object(self, model: Type[Base] = None, obj_id: uuid = None) -> None:
        """
        Delete an object by its ID from the database. Rolls back if the operation fails.
        
        :param model: The model type to delete.
        :param obj_id: The unique ID of the object to delete.
        :raise SQLAlchemyError: If the database operation fails.
        """
        db = self.Session()
        try:
            obj = db.query(model).filter(model.id == obj_id).first()
            if obj:
                db.delete(obj)
                db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def _get_subquery(self) -> Subquery:
        """
        Returns subquery for loan state last blocks query.
        
        :return: A Subquery with the latest block for each user.
        """
        session = self.Session()
        return (
            session.query(
                LoanState.user, func.max(LoanState.block).label("latest_block")
            )
            .group_by(LoanState.user)
            .subquery()
        )

    def get_latest_block_loans(self) -> List[LoanState]:
        """
        Returns a query with the latest block for each loan state.
        
        :return: A list of LoanState objects.
        """
        session = self.Session()
        subquery = self._get_subquery()
        result = (
            session.query(LoanState)
            .join(
                subquery,
                and_(
                    LoanState.user == subquery.c.user,
                    LoanState.block == subquery.c.latest_block,
                ),
            )
            .all()
        )
        return result

    def get_loans(
        self,
        model: Type[Base],
        protocol: Optional[str] = None,
        user: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        start_datetime: Optional[int] = None,
        end_datetime: Optional[int] = None,
    ) -> List[Base]:
        """
        Retrieves loans based on various search criteria.
        
        :param model: The model type to query.
        :param protocol: The protocol ID to filter by.
        :param user: The user ID to filter by.
        :param start_block: Minimum block number.
        :param end_block: Maximum block number.
        :param start_datetime: Minimum timestamp.
        :param end_datetime: Maximum timestamp.
        :return: A list of model objects matching the criteria.
        """
        db = self.Session()
        try:
            query = db.query(model)
            if protocol:
                query = query.filter(model.protocol_id == protocol)
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

    def get_last_hashstack_loan_state(self, user_id: str) -> Optional[HashtackCollateralDebt]:
        """
        Retrieves the last loan state for a given user ID.
        
        :param user_id: The user ID to filter by.
        :return: A HashtackCollateralDebt object or None.
        """
        db = self.Session()
        try:
            return (
                db.query(HashtackCollateralDebt)
                .filter(HashtackCollateralDebt.user_id == user_id)
                .order_by(HashtackCollateralDebt.loan_id.desc())
                .first()
            )
        finally:
            db.close()

    def get_last_block(self, protocol_id: ProtocolIDs) -> int:
        """
        Retrieves the highest block number filtered by protocol ID.
        
        :param protocol_id: The protocol ID to filter by.
        :return: The highest block number as an integer.
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
        Writes a batch of objects to the database.
        
        :param objects: List of Base instances to write.
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
        Writes a batch of loan states to the database, updating existing ones if needed.
        
        :param objects: List of LoanState instances to write.
        :raise SQLAlchemyError: If the database operation fails.
        """
        db: Session = self.Session()
        loan_data = [
            {
                "protocol_id": obj.protocol_id,
                "user": obj.user,
                "collateral": obj.collateral,
                "debt": obj.debt,
                "timestamp": obj.timestamp,
                "block": obj.block,
                "deposit": obj.deposit,
            }
            for obj in objects
        ]
        try:
            stmt = insert(LoanState).values(loan_data)
            update_dict = {
                "collateral": stmt.excluded.collateral,
                "debt": stmt.excluded.debt,
            }
            stmt = stmt.on_conflict_do_update(
                constraint="loan_state_protocol_id_user_key", set_=update_dict
            )
            db.execute(stmt)
            logger.info(f"Updating or adding {len(objects)} loan states to the database.")
            db.commit()
            logger.info(f"Successfully updated or added {len(objects)} loan states.")
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_latest_order_book(
        self, dex: str, token_a: str, token_b: str
    ) -> Optional[OrderBookModel]:
        """
        Retrieves the latest order book for a token pair on a specific DEX.
        
        :param dex: The DEX name.
        :param token_a: The base token address.
        :param token_b: The quote token address.
        :return: The latest OrderBookModel instance or None.
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
                .where(order_book_condition)
