from fastapi import Body, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from database.crud import validate_fields, write_to_db
from database.database import Base, engine, get_database
from database.models import NotificationData
from database.schemas import Notification
from utils.values import CreateSubscriptionValues, NotificationValidationValues

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post(
    path="/create-notifications-subscription",
    description=CreateSubscriptionValues.create_subscription_description_message,
)
async def create_subscription_to_notifications(
    data: Notification = Body(...), db: Session = Depends(get_database)
):
    """
    Creates a new subscription to notifications
    :param data: Notification
    :param db: Session
    :return: dict
    """
    if not all(
        [
            value
            for key, value in data.model_dump().items()
            if key in NotificationValidationValues.validation_fields
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CreateSubscriptionValues.create_subscription_exception_message,
        )

    subscription = NotificationData(**data.model_dump())
    validation_errors = validate_fields(db=db, obj=subscription, model=NotificationData)

    if validation_errors:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=validation_errors
        )

    write_to_db(db=db, obj=subscription)

    return {
        "message": CreateSubscriptionValues.create_subscription_success_message,
        "status": status.HTTP_201_CREATED,
    }
