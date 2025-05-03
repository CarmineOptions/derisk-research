from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from loguru import logger

from app.utils.watcher_mixin import WatcherMixin
from app.crud.base import db_connector
from app.db.session import get_db
from app.models.watcher import NotificationData
from app.schemas import NotificationForm
# from telegram import get_subscription_link    #FIXME
from app.utils.fucntools import get_client_ip
from app.utils.values import CreateSubscriptionValues, ProtocolIDs, NotificationValidationValues

router = APIRouter()


@router.post(
    path="/liquidation-watcher",
    description=CreateSubscriptionValues.create_subscription_description_message,
)
async def subscribe_to_notification(
    request: Request,
    data: NotificationForm,
    db: Session = Depends(get_db),
):
    """
    Creates a new subscription for notifications
    :param request: Request
    :param data: NotificationForm
    :param db: Session
    :return: dict
    """
    # assign client IP for record
    data.ip_address = get_client_ip(request)

    if not all(
        [
            value
            for key, value in data.model_dump().items()
            if key in NotificationValidationValues.validation_fields
        ]
    ):
        logger.error(
            f"User with {get_client_ip(request)} IP submits with a lack of all required fields"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "messages": [CreateSubscriptionValues.create_subscription_exception_message],
                "message_type": "error",
                "protocol_ids": [item.value for item in ProtocolIDs],
            },
        )

    subscription = NotificationData(**data.model_dump())
    validation_errors = WatcherMixin.validate_fields(db=db, obj=subscription, model=NotificationData)

    if validation_errors:
        logger.error(f"User with {get_client_ip(request)} IP submits with invalid data")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "messages": list(validation_errors.values()),
                "message_type": "error",
                "protocol_ids": [item.value for item in ProtocolIDs],
            },
        )

    subscription_id = db_connector.write_to_db(obj=subscription)

    # activation_link = await get_subscription_link(ident=subscription_id)  #FIXME
    logger.info(f"Activation link for user with {get_client_ip(request)} IP is sent")

    logger.info(f"User with {get_client_ip(request)} IP submitted successfully")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status_code": status.HTTP_201_CREATED,
            "messages": [CreateSubscriptionValues.create_subscription_success_message],
            "message_type": "success",
            # "activation_link": activation_link, # FIXME unccomend once telegram is ready
            "protocol_ids": [item.value for item in ProtocolIDs],
        },
    )

@router.get(
    path="/protocol-ids",
    description="Returns a list of valid protocol IDs"
)
async def get_protocol_ids() -> JSONResponse:
    """
    Returns all protocol IDs defined in the backend.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"protocol_ids": [item.value for item in ProtocolIDs]},
    )
