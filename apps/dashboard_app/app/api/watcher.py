import asyncio
from datetime import datetime

from dashboard_app.app.telegram_app.telegram import bot
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.orm import Session

from dashboard_app.app.crud.base import db_connector
from dashboard_app.app.models.watcher import NotificationData, ProtocolIDs
from dashboard_app.app.schemas import NotificationForm
from dashboard_app.app.telegram_app.telegram import TelegramNotifications
from dashboard_app.app.telegram_app.telegram.utils import get_subscription_link

from dashboard_app.app.utils.fucntools import (
    calculate_difference,
    get_all_activated_subscribers_from_db,
    get_client_ip,
    get_health_ratio_level_from_endpoint,
)
from dashboard_app.app.utils.values import (
    HEALTH_RATIO_LEVEL_ALERT_VALUE,
    CreateSubscriptionValues,
    NotificationValidationValues,
)
from dashboard_app.app.utils.watcher_mixin import WatcherMixin

router = APIRouter()
notificator = TelegramNotifications(db_connector=db_connector)


@router.post(
    path="/liquidation-watcher",
    description=CreateSubscriptionValues.create_subscription_description_message,
)
async def subscribe_to_notification(
    request: Request,
    data: NotificationForm,
    db: Session = Depends(db_connector.get_db),
):
    """
    Creates a new subscription for notifications
    :param request: Request
    :param data: NotificationForm
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
        logger.error(
            f"User with {get_client_ip(request)} IP submits with a lack of all required fields"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "messages": [
                    CreateSubscriptionValues.create_subscription_exception_message
                ],
                "message_type": "error",
                "protocol_ids": [item.value for item in ProtocolIDs],
            },
        )

    subscription = NotificationData(**data.model_dump())
    # assign client IP for record
    subscription.ip_address = get_client_ip(request)
    validation_errors = WatcherMixin.validate_fields(
        db=db, obj=subscription, model=NotificationData
    )

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

    subscription = await db_connector.write_to_db(obj=subscription)
    activation_link = await get_subscription_link(ident=subscription.id)
    logger.info(f"Activation link for user with {get_client_ip(request)} IP is sent")

    logger.info(f"User with {get_client_ip(request)} IP submitted successfully")
    try:
        await bot.send_message(
            chat_id=subscription.telegram_id,
            text=f"You have been subscribed to receive updates.\n Protocol: {str(subscription.protocol_id).split('.')[1]}, Health ratio:{subscription.health_ratio_level}",
        )
    except Exception:
        logger.error(f"Unable send telegram message")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "status_code": status.HTTP_201_CREATED,
            "messages": [CreateSubscriptionValues.create_subscription_success_message],
            "message_type": "success",
            "activation_link": activation_link,
            "protocol_ids": [item.value for item in ProtocolIDs],
        },
    )


@router.get(path="/protocol-ids", description="Returns a list of valid protocol IDs")
async def get_protocol_ids() -> JSONResponse:
    """
    Returns all protocol IDs defined in the backend.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"protocol_ids": [item.value for item in ProtocolIDs]},
    )


@router.post(
    path="/send-notifications", description="Send notifications to all subscribers"
)
async def send_notifications() -> None:
    """
    Sends notifications to all activated subscribers when their health ratio level
    changes significantly.

    Returns:
        None
    """

    subscribers = await get_all_activated_subscribers_from_db()

    for subscriber in subscribers:
        health_ratio_level = get_health_ratio_level_from_endpoint(
            protocol_id=subscriber.protocol_id.value, user_id=subscriber.wallet_id
        )

        if (
            calculate_difference(health_ratio_level, subscriber.health_ratio_level)
            >= HEALTH_RATIO_LEVEL_ALERT_VALUE
        ):
            asyncio.run(notificator.send_notification(notification_id=subscriber.id))

    asyncio.run(notificator(is_infinity=True))
