"""Classes:
- DBConnector: Manages database connections and CRUD operations.
- InitializerDBConnector: Handles ZkLendCollateralDebt-specific operations.
- NostraEventDBConnector: Manages Nostra event-specific operations.
- ZkLendEventDBConnector: Manages ZkLend event-specific operations."""

import logging
import uuid
from typing import List, Optional, Type, TypeVar

from apps.data_handler.db.database import SQLALCHEMY_DATABASE_URL
from apps.data_handler.db.models import (
    Base,
    InterestRate,
    LoanState,
    OrderBookModel,
    ZkLendCollateralDebt,
)
from apps.data_handler.db.models.nostra_events import (
    BearingCollateralBurnEventModel,
    BearingCollateralMintEventModel,
    DebtBurnEventModel,
    DebtMintEventModel,
    DebtTransferEventModel,
    InterestRateModelEventModel,
    NonInterestBearingCollateralBurnEventModel,
    NonInterestBearingCollateralMintEventModel,
)
from apps.data_handler.db.models.zklend_events import (
    AccumulatorsSyncEventModel,
    BorrowingEventModel,
    CollateralEnabledDisabledEventModel,
    DepositEventModel,
    LiquidationEventModel,
    RepaymentEventModel,
    WithdrawalEventModel,
)
from apps.shared.constants import ProtocolIDs
from sqlalchemy import Subquery, and_, create_engine, desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, aliased, scoped_session, sessionmaker

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
        If an object already exists in the database (based on protocol_id and user),
        it will be updated with the new values instead of creating a new instance.
        :param objects: List[LoanState] - A list of LoanState instances to write.
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
            # Use PostgreSQL's insert with on_conflict_do_update for upserting records
            stmt = insert(LoanState).values(loan_data)
            update_dict = {
                "collateral": stmt.excluded.collateral,
                "debt": stmt.excluded.debt,
            }
            stmt = stmt.on_conflict_do_update(
                constraint="loan_state_protocol_id_user_key", set_=update_dict
            )

            # Execute the upsert statement
            db.execute(stmt)

            logger.info(
                f"Updating or adding {len(objects)} loan states to the database."
            )

            # Commit the changes
            db.commit()
            logger.info(f"Successfully updated or added {len(objects)} loan states.")

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
        Fetch the closest InterestRate instance by block number that is less than or equal
        to the given block number.

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

    def get_all_events_from_models(
        self,
        models: List[Type[ModelType]],
        protocol_id: Optional[str] = None,
        event_name: Optional[str] = None,
        block_number: Optional[int] = None,
    ) -> List[Base]:
        """
        Retrieves events from multiple models based on filtering criteria.

        :param models: List of SQLAlchemy models to query.
        :param protocol_id: Optional protocol ID to filter by.
        :param event_name: Optional event name to filter by.
        :param block_number: Optional block number to filter by.
        :return: A combined list of events from all specified models.
        """
        events = []
        db = self.Session()
        try:
            for model in models:
                model_filters = []
                if protocol_id:
                    model_filters.append(model.protocol_id == protocol_id)
                if event_name:
                    model_filters.append(model.event_name == event_name)
                if block_number:
                    model_filters.append(model.block_number == block_number)

                query = db.query(model)
                if model_filters:
                    query = query.filter(*model_filters)

                fetched_events = query.all()
                events.extend(fetched_events)
            return events
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving events from models {models}: {e}")
            raise e
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

class ZkLendEventDBConnector(DBConnector):
    """
    Provides CRUD operations specifically for ZkLend events, such as accumulator sync
    and liquidation events.
    Methods:
    - create_accumulator_event: Creates an AccumulatorsSyncEventModel record.
    - create_liquidation_event: Creates a LiquidationEventModel record.
    - get_all_events: Retrieves events based on filtering criteria such as protocol_id,
    event_name, or block_number.
    """

    def create_accumulator_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates an AccumulatorsSyncEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'token', 'lending_accumulator', and
        'debt_accumulator'.
        """
        event = AccumulatorsSyncEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            token=event_data.get("token"),
            lending_accumulator=event_data.get("lending_accumulator"),
            debt_accumulator=event_data.get("debt_accumulator"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"AccumulatorsSyncEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating AccumulatorsSyncEventModel: {e}")
            raise e

    def create_liquidation_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a LiquidationEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'liquidator', 'user', 'debt_token',
        'debt_raw_amount', 'debt_face_amount',
        'collateral_token', and 'collateral_amount'.
        """
        event = LiquidationEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            liquidator=event_data.get("liquidator"),
            user=event_data.get("user"),
            debt_token=event_data.get("debt_token"),
            debt_raw_amount=event_data.get("debt_raw_amount"),
            debt_face_amount=event_data.get("debt_face_amount"),
            collateral_token=event_data.get("collateral_token"),
            collateral_amount=event_data.get("collateral_amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"LiquidationEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating LiquidationEventModel: {e}")
            raise e

    def create_repayment_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a RepaymentEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'user', 'amount'.
        """
        event = RepaymentEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            repayer=event_data.get("repayer"),
            beneficiary=event_data.get("beneficiary"),
            token=event_data.get("token"),
            raw_amount=event_data.get("raw_amount"),
            face_amount=event_data.get("face_amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"RepaymentEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating RepaymentEventModel: {e}")
            raise e

    def create_borrowing_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a BorrowingEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'user', 'token', 'raw_amount', 'face_amount'.
        """
        event = BorrowingEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            token=event_data.get("token"),
            raw_amount=event_data.get("raw_amount"),
            face_amount=event_data.get("face_amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"BorrowingEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating BorrowingEventModel: {e}")
            raise e

    def create_deposit_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a DepositEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'user', 'token', 'face_amount'.
        """
        event = DepositEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            token=event_data.get("token"),
            face_amount=event_data.get("face_amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"DepositEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating DepositEventModel: {e}")
            raise e

    def create_withdrawal_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a WithdrawalEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'user', 'token', 'face_amount'.
        """
        event = WithdrawalEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            token=event_data.get("token"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"WithdrawalEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating WithdrawalEventModel: {e}")
            raise e

    def create_collateral_enabled_disabled_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a CollateralEnabledDisabledEventModel record in the database.
        :param protocol_id: The protocol ID for the event.
        :param event_name: The name of the event.
        :param block_number: The block number associated with the event.
        :param event_data: A dictionary containing 'user', 'token'.
        """
        event = CollateralEnabledDisabledEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            token=event_data.get("token"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"CollateralEnabledDisabledEvent saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating CollateralEnabledDisabledEventModel: {e}")
            raise e

    def get_all_events(
        self,
        protocol_id: Optional[str] = None,
        event_name: Optional[str] = None,
        block_number: Optional[int] = None,
    ) -> List[Base]:
        """
        Retrieves events based on filtering criteria such as protocol_id,
        event_name, or block_number.
        :param protocol_id: Optional protocol ID to filter by.
        :param event_name: Optional event name to filter by.
        :param block_number: Optional block number to filter by.
        :return: A list of events matching the criteria.
        """
        event_models = [
            AccumulatorsSyncEventModel,
            LiquidationEventModel,
            RepaymentEventModel,
            BorrowingEventModel,
            DepositEventModel,
            WithdrawalEventModel,
            CollateralEnabledDisabledEventModel,
        ]

        try:
            events = self.get_all_events_from_models(
                models=event_models,
                protocol_id=protocol_id,
                event_name=event_name,
                block_number=block_number,
            )
            return events
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving ZkLend events: {e}")
            raise e


class NostraEventDBConnector(DBConnector):
    """
    Provides CRUD operations specifically for Nostra events, such as
    BearingCollateralBurn, BearingCollateralMint, DebtMint, DebtBurn, DebtTransfer,
    InterestRateModelUpdate, NonInterestBearingCollateralMint and NonInterestBearingCollateralMint events.
    """

    def create_bearing_collateral_burn_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a BearingCollateralBurnEventModel record in the database.
        """
        event = BearingCollateralBurnEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"BearingCollateralBurn event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating BearingCollateralBurnEventModel: {e}")
            raise e

    def create_bearing_collateral_mint_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a BearingCollateralMintEventModel record in the database.
        """
        event = BearingCollateralMintEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"BearingCollateralMint event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating BearingCollateralMintEventModel: {e}")
            raise e

    def create_debt_burn_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a DebtBurnEventModel record in the database.
        """
        event = DebtBurnEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"DebtBurn event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating DebtBurnEventModel: {e}")
            raise e

    def create_debt_mint_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a DebtMintEventModel record in the database.
        """
        event = DebtMintEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"DebtMint event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating DebtMintEventModel: {e}")
            raise e

    def create_debt_transfer_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a DebtTransferEventModel record in the database.
        """
        event = DebtTransferEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            sender=event_data.get("sender"),
            recipient=event_data.get("recipient"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"DebtTransfer event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating DebtTransferEventModel: {e}")
            raise e

    def create_interest_rate_model_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a InterestRateModelEventModel record in the database.
        """
        event = InterestRateModelEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            debt_token=event_data.get("debt_token"),
            lending_index=event_data.get("lending_index"),
            borrow_index=event_data.get("borrow_index"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"InterestRateModel event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(f"Error creating InterestRateModelEventModel: {e}")
            raise e

    def create_non_interest_bearing_collateral_burn_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a NonInterestBearingCollateralBurnEventModel record in the database.
        """
        event = NonInterestBearingCollateralBurnEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            user=event_data.get("user"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"NonInterestBearingCollateralBurn event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(
                f"Error creating NonInterestBearingCollateralBurnEventModel: {e}"
            )
            raise e

    def create_non_interest_bearing_collateral_mint_event(
        self, protocol_id: str, event_name: str, block_number: int, event_data: dict
    ) -> None:
        """
        Creates a NonInterestBearingCollateralMintEventModel record in the database.
        """
        event = NonInterestBearingCollateralMintEventModel(
            protocol_id=protocol_id,
            event_name=event_name,
            block_number=block_number,
            sender=event_data.get("sender"),
            recipient=event_data.get("recipient"),
            amount=event_data.get("amount"),
        )
        try:
            self.write_to_db(event)
            logger.info(f"NonInterestBearingCollateralMint event saved: {event}")
        except SQLAlchemyError as e:
            logger.error(
                f"Error creating NonInterestBearingCollateralMintEventModel: {e}"
            )
            raise e

    def get_all_events(
        self,
        protocol_id: Optional[str] = None,
        event_name: Optional[str] = None,
        block_number: Optional[int] = None,
    ) -> List:
        """
        Retrieves all types of Nostra events based on filtering criteria.
        """
        event_models = [
            BearingCollateralBurnEventModel,
            BearingCollateralMintEventModel,
            DebtBurnEventModel,
            DebtMintEventModel,
            DebtTransferEventModel,
            InterestRateModelEventModel,
            NonInterestBearingCollateralBurnEventModel,
            NonInterestBearingCollateralMintEventModel,
        ]

        try:
            events = self.get_all_events_from_models(
                models=event_models,
                protocol_id=protocol_id,
                event_name=event_name,
                block_number=block_number,
            )
            return events
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving Nostra events: {e}")
            raise e
