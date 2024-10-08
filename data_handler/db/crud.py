import logging
import uuid
from typing import List, Optional, Type, TypeVar

from handler_tools.constants import ProtocolIDs
from sqlalchemy import Subquery, and_, create_engine, desc, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, aliased, scoped_session, sessionmaker

from db.database import SQLALCHEMY_DATABASE_URL
from db.models import (
    Base,
    HashtackCollateralDebt,
    InterestRate,
    LoanState,
    OrderBookModel,
    ZkLendCollateralDebt,
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

    def _get_subquery(self) -> Subquery:
        """
        Returns subquery for loan state last blocks query
        :return: Subquery
        """
        session = self.Session()
        return (
            session.query(
                LoanState.user, func.max(LoanState.block).label("latest_block")
            )
            .group_by(LoanState.user)
            .subquery()
        )

    def get_latest_block_loans(self) -> Query:
        """
        Returns a lastt block query
        :return: Last block query
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
    ):
        """
        Retrieves loans based on various search criteria.
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

    def get_last_hashstack_loan_state(self, user_id: str) -> HashtackCollateralDebt:
        """
        Retrieves the last loan state for a given user_id.
        :param user_id: str - The user ID to filter by.
        :return: HashtackCollateralDebt | None
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

            logger.info(f"Saving {len(objects_to_save)} loan states to the database.")
            # Save the filtered objects
            if objects_to_save:
                db.bulk_save_objects(objects_to_save)
                db.commit()
                logger.info(
                    f"Saved {len(objects_to_save)} loan states to the database."
                )
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
            logging.info("Loan states have been written to the database.")

    def get_latest_order_book(
        self, dex: str, token_a: str, token_b: str
    ) -> OrderBookModel | None:
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
                .where(order_book_condition)
                .scalar_subquery()
            )
            return db.execute(
                select(OrderBookModel).where(
                    OrderBookModel.timestamp == max_timestamp, order_book_condition
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

    def get_interest_rate_by_block(
        self, block_number: int, protocol_id: str
    ) -> InterestRate:
        """
        Fetch the closest InterestRate instance by block number that is less than or equal to the given block number.

        :param protocol_id: The protocol ID to search for.
        :param block_number: The block number to search for.
        :return: An instance of InterestRate or None if no such instance exists.
        """
        db = self.Session()
        try:
            return (
                db.query(InterestRate)
                .filter(InterestRate.protocol_id == protocol_id)
                .filter(InterestRate.block <= block_number)
                .order_by(desc(InterestRate.block))
                .first()
            )
        finally:
            db.close()

    def get_all_block_records(self, model: Type[ModelType] = None) -> Query:
        """
        Retrieves all rows of given model in descending order.
        :param model: Type - The model to get data from.
        :return: Query - The query of all block records.
        """
        db = self.Session()
        try:
            return db.query(
                model.user,
                model.collateral,
                model.debt,
            ).order_by(desc(model.block))
        finally:
            db.close()


class InitializerDBConnector:
    """
    Provides database connection and CRUD operations for ZkLendCollateralDebt.

    Methods:
    - get_by_user_id: Retrieves ZkLendCollateralDebt record by user_id.
    - update_by_user_id: Updates the collateral and debt by user_id.
    """

    def __init__(self, db_url: str = SQLALCHEMY_DATABASE_URL):
        """
        Initialize the database connection and session factory.
        :param db_url: Database connection URL.
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def get_zklend_by_user_ids(self, user_ids: List[str]) -> List[ZkLendCollateralDebt]:
        """
        Retrieve ZkLendCollateralDebt records by user_ids.
        :param user_ids: A list of user IDs to filter by.
        :return: A list of ZkLendCollateralDebt objects.
        """
        session = self.Session()
        try:
            return (
                session.query(ZkLendCollateralDebt)
                .filter(ZkLendCollateralDebt.user_id.in_(user_ids))
                .all()
            )
        finally:
            session.close()

    def get_hashtack_by_loan_ids(
        self, loan_ids: List[str], version: int
    ) -> List[HashtackCollateralDebt]:
        """
        Retrieve HashtackCollateralDebt records by loan_ids.
        :param loan_ids: A list of user IDs to filter by.
        :param version: The version of the hashtack.
        :return: A list of HashtackCollateralDebt objects.
        """
        session = self.Session()
        try:
            return (
                session.query(HashtackCollateralDebt)
                .filter(HashtackCollateralDebt.loan_id.in_(loan_ids))
                .filter(HashtackCollateralDebt.version == version)
                .all()
            )
        finally:
            session.close()

    @staticmethod
    def _convert_decimal_to_float(data: dict | None) -> dict | None:
        """
        Convert Decimal values to float for a given dictionary.
        :param data: The dictionary to convert.
        :return: The converted dictionary or None
        """
        if data:
            return {k: float(v) for k, v in data.items()}

        return None

    def save_collateral_enabled_by_user(
        self,
        user_id: str,
        collateral_enabled: dict,
        collateral: dict = None,
        debt: dict = None,
    ) -> None:
        """
        Update the collateral and debt for a given user_id.
        :param user_id: The user ID to update.
        :param collateral: The new collateral data.
        :param debt: The new debt data.
        :param collateral_enabled: The new collateral enabled data.

        :return: None
        """
        session = self.Session()
        collateral = self._convert_decimal_to_float(collateral)
        debt = self._convert_decimal_to_float(debt)
        try:
            record = (
                session.query(ZkLendCollateralDebt).filter_by(user_id=user_id).first()
            )
            if record:
                # Update existing record
                if collateral is not None:
                    record.collateral = collateral
                if debt is not None:
                    record.debt = debt
                record.collateral_enabled = collateral_enabled
            else:
                # Create new record
                new_record = ZkLendCollateralDebt(
                    user_id=user_id,
                    collateral=collateral if collateral is not None else {},
                    debt=debt if debt is not None else {},
                    deposit={},
                    collateral_enabled=collateral_enabled,
                )
                session.add(new_record)
            session.commit()
        finally:
            session.close()

    def save_debt_category(
        self,
        user_id: str,
        loan_id: str,
        debt_category: str,
        collateral: dict,
        debt: dict,
        original_collateral: dict,
        borrowed_collateral: dict,
        version: int,
    ) -> None:
        """
        Update the debt category for a given user_id.
        :param user_id: The user ID to update.
        :param loan_id: The loan ID to update.
        :param debt_category: The new debt category.
        :param collateral: The new collateral data.
        :param debt: The new debt data.
        :param original_collateral: The new original collateral data.
        :param borrowed_collateral: The new borrowed collateral data.
        :param version: The version of the hashtack.
        :return: None
        """
        session = self.Session()
        # convert Decimal to float for JSON serialization
        collateral = self._convert_decimal_to_float(collateral)
        debt = self._convert_decimal_to_float(debt)
        original_collateral = self._convert_decimal_to_float(original_collateral)
        borrowed_collateral = self._convert_decimal_to_float(borrowed_collateral)

        try:
            record = (
                session.query(HashtackCollateralDebt).filter_by(loan_id=loan_id).first()
            )
            logger.info(f"Going to save loan_id {loan_id}")
            # if debt category is the same, update the record
            if record and record.debt_category == debt_category:
                return
            # if record exists, and debt category is different, update the record
            elif record and record.debt_category != debt_category:
                record.loan_id = loan_id
                record.debt_category = debt_category
                record.collateral = collateral
                record.debt = debt
                record.original_collateral = original_collateral
                record.borrowed_collateral = borrowed_collateral
            else:
                # Create new record if not yet created for this user
                new_record = HashtackCollateralDebt(
                    user_id=user_id,
                    loan_id=loan_id,
                    # collateral
                    collateral=collateral,
                    original_collateral=original_collateral,
                    # debt
                    debt=debt,
                    borrowed_collateral=borrowed_collateral,
                    debt_category=debt_category,
                    version=version,
                )
                session.add(new_record)
            session.commit()
            logger.info(f"Saved debt category for loan_id {loan_id}")
        finally:
            session.close()
