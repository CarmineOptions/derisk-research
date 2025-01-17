from typing import Type, TypeVar
from uuid import UUID

from database.database import SQLALCHEMY_DATABASE_URL
from database.models import Base
from sqlalchemy import create_engine, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from utils.values import (
    CURRENTLY_AVAILABLE_PROTOCOLS_IDS,
    CreateSubscriptionValues,
    NotificationValidationValues,
)

ModelType = TypeVar("ModelType", bound=Base)


def _exists_in_db(
    db: Session = None,
    model: Type[Base] = None,
    attr: str = None,
    obj: Base = None,
) -> bool:
    """
    Checks if the given attribute value already exists in the database
    :param db: Session = Depends(get_database)
    :param model: type[Base] = None
    :param attr: str = None
    :param obj: Base = None
    :return: bool
    """
    return (
        db.query(model).filter(getattr(model, attr) == getattr(obj, attr)).first()  # type: ignore
        is not None
    )


def health_ratio_is_valid(health_ratio: float) -> bool:
    """
    Checks if the given health ratio level value is valid
    :param health_ratio: float
    :return: bool
    """
    return (
        NotificationValidationValues.health_ratio_level_min_value
        <= health_ratio
        <= NotificationValidationValues.health_ratio_level_max_value
    )


def validate_health_ratio(health_ratio: float = None) -> dict[str, str] | None:
    """
    Validates the health ratio level
    :param health_ratio: float
    :return: dict[str, str]
    """
    if not health_ratio_is_valid(health_ratio):
        return {
            "health_ratio_level": CreateSubscriptionValues.health_ratio_level_validation_message
        }

    return None


def validate_fields(
    db: Session = None, obj: ModelType = None, model: Type[ModelType] = None
) -> dict:
    """
    Validates all fields in the object and returns a dict with validation errors if they were occurred
    :param db: Session = Depends(get_database)
    :param obj: Base = None
    :param model: type[Base] = None
    :return: dict
    """
    error_validation_dict = dict()
    _fields = NotificationValidationValues.unique_fields

    for attr in dir(obj):
        if (attr in _fields) and _exists_in_db(db=db, model=model, attr=attr, obj=obj):
            field_name = " ".join(str(attr).split("_"))
            error_validation_dict.update(
                {f"{attr}": f"Current {field_name} is already taken"}
            )

    if health_ratio_validation_message := validate_health_ratio(obj.health_ratio_level):
        error_validation_dict.update(health_ratio_validation_message)

    return error_validation_dict


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

    def write_to_db(self, obj: Base = None) -> str:
        """
        Writes an object to the database. Rolls back transaction if there's an error.
        :param obj: Base = None
        :raise SQLAlchemyError: If the database operation fails.
        :return: str
        """
        db = self.Session()
        try:
            db.add(obj)
            db.commit()

        except SQLAlchemyError as e:
            db.rollback()
            raise e

        finally:
            object_id = getattr(obj, "id", "")
            db.close()

            return object_id

    def get_object(
        self, model: Type[ModelType] = None, obj_id: UUID = None
    ) -> ModelType | None:
        """
        Retrieves an object by its ID from the database.
        :param: model: type[Base] = None
        :param: obj_id: UUID = None
        :return: Base | None
        """
        db = self.Session()
        try:
            return db.query(model).filter(model.id == obj_id).first()
        finally:
            db.close()

    def get_all_activated_subscribers(
        self, model: Type[Base] = None
    ) -> ModelType | None:
        db = self.Session()
        try:
            return (
                db.query(model)
                .filter(
                    func.char_length(model.telegram_id)
                    >= NotificationValidationValues.telegram_id_min_length,
                    model.protocol_id.in_(CURRENTLY_AVAILABLE_PROTOCOLS_IDS),
                )
                .all()
            )
        finally:
            db.close()

    def delete_object(self, model: Type[Base] = None, obj_id: UUID = None) -> None:
        """
        Delete an object by its ID from the database. Rolls back if the operation fails.
        :param model: type[Base] = None
        :param obj_id: UUID = None
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
