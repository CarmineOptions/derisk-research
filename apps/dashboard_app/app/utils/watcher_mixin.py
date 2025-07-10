from typing import Type

from sqlalchemy.orm import Session

from shared.db import ModelType, Base
from ..utils.values import CreateSubscriptionValues, NotificationValidationValues


class WatcherMixin:
    @staticmethod
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
            db.query(model).filter(getattr(model, attr) == getattr(obj, attr)).first()
            is not None
        )

    @staticmethod
    def health_ratio_is_valid(health_ratio: float) -> bool:
        """
        Checks if the given health ratio level value is valid
        :param health_ratio: float
        :return: bool
        """
        if health_ratio is None:
            return False
        return (
            NotificationValidationValues.health_ratio_level_min_value
            <= health_ratio
            <= NotificationValidationValues.health_ratio_level_max_value
        )

    @staticmethod
    def validate_health_ratio(health_ratio: float = None) -> dict[str, str] | None:
        """
        Validates the health ratio level
        :param health_ratio: float
        :return: dict[str, str]
        """
        if not WatcherMixin.health_ratio_is_valid(health_ratio):
            return {
                "health_ratio_level": CreateSubscriptionValues.health_ratio_level_validation_message
            }

    @staticmethod
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
            if (attr in _fields) and WatcherMixin._exists_in_db(
                db=db, model=model, attr=attr, obj=obj
            ):
                field_name = " ".join(str(attr).split("_"))
                error_validation_dict.update(
                    {f"{attr}": f"Current {field_name} is already taken"}
                )

        if health_ratio_validation_message := WatcherMixin.validate_health_ratio(
            obj.health_ratio_level
        ):
            error_validation_dict.update(health_ratio_validation_message)

        return error_validation_dict
