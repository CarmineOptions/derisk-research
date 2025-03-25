from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from loguru import logger

from database.crud import DBConnector, validate_fields
from database.database import get_database
from database.models import NotificationData
from database.schemas import NotificationForm
# from telegram import get_subscription_link    #FIXME
from utils.fucntools import get_client_ip
from utils.values import (
    CreateSubscriptionValues,
    NotificationValidationValues,
    ProtocolIDs,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")
connector = DBConnector()

@router.get(
    path="/liquidation-watcher",
    description=CreateSubscriptionValues.create_subscription_description_message,
    response_class=HTMLResponse,
)
async def create_subscription(request: Request) -> HTMLResponse:
    """
    Returns a subscription for notifications form
    :param request: Request
    :return: templates.TemplateResponse
    """
    logger.info(f"User with {get_client_ip(request)} IP is accessing the page")
    return templates.TemplateResponse(
        request=request,
        name="notification.html",
        context={
            "protocol_ids": [item.value for item in ProtocolIDs],
        },
    )

@router.post(
    path="/liquidation-watcher",
    description=CreateSubscriptionValues.create_subscription_description_message,
)
async def subscribe_to_notification(
    request: Request,
    data: NotificationForm = Depends(NotificationForm.as_form),
    db: Session = Depends(get_database),
):
    """
    Creates a new subscription for notifications
    :param request: Request
    :param data: NotificationForm
    :param db: Session
    :return: dict
    """
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
        return templates.TemplateResponse(
            request=request,
            name="notification.html",
            context={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "messages": [
                    CreateSubscriptionValues.create_subscription_exception_message
                ],
                "message_type": "error",
                "protocol_ids": [item.value for item in ProtocolIDs],
            },
        )

    subscription = NotificationData(**data.model_dump())
    validation_errors = validate_fields(db=db, obj=subscription, model=NotificationData)

    if validation_errors:
        logger.error(f"User with {get_client_ip(request)} IP submits with invalid data")
        return templates.TemplateResponse(
            request=request,
            name="notification.html",
            context={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "messages": list(validation_errors.values()),
                "message_type": "error",
                "protocol_ids": [item.value for item in ProtocolIDs],
            },
        )

    subscription_id = connector.write_to_db(obj=subscription)

    # activation_link = await get_subscription_link(ident=subscription_id)  #FIXME
    logger.info(f"Activation link for user with {get_client_ip(request)} IP is sent")

    logger.info(f"User with {get_client_ip(request)} IP submitted successfully")
    return templates.TemplateResponse(
        request=request,
        name="notification.html",
        context={
            "status_code": status.HTTP_201_CREATED,
            "messages": [CreateSubscriptionValues.create_subscription_success_message],
            "message_type": "success",
            "activation_link": activation_link,
            "protocol_ids": [item.value for item in ProtocolIDs],
        },
    )
