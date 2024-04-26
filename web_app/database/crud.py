from typing import Any

from sqlalchemy.orm import Session

from utils.values import NotificationValidationValues


def _exists_in_db(
    db: Session = None,
    model: Any = None,
    attr: Any = None,
    obj: Any = None,
) -> bool:
    """
    Checks if the given attribute value already exists in the database
    :param db: Session = Depends(get_database)
    :param model: Any = None
    :param attr: attr: Any = None
    :param obj: Any = None
    :return: bool
    """
    return (
        db.query(model).filter(getattr(model, attr) == getattr(obj, attr)).first()
        is not None
    )


def validate_fields(db: Session = None, obj: Any = None, model: Any = None) -> dict:
    """
    Validates all fields in the object a dict with exceptions if they were occured
    :param db: Session = Depends(get_database)
    :param obj: Any = None
    :param model: Any = None
    :return: dict
    """
    exceptions_dict = dict()
    _fields = NotificationValidationValues.validation_fields

    for attr in dir(obj):
        if (attr in _fields) and _exists_in_db(db=db, model=model, attr=attr, obj=obj):
            field_name = " ".join(str(attr).split("_"))
            exceptions_dict.update(
                {f"{attr}": f"Current {field_name} is already taken"}
            )

    return exceptions_dict


def write_to_db(db: Session = None, obj: Any = None) -> None:
    """
    Implements write operation to database
    :param db: Session = None
    :param obj: Any = None
    :return: None
    """
    db.add(obj)
    db.commit()
    db.refresh(obj)
