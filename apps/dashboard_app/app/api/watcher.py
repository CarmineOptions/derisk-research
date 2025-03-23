from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from loguru import logger

from utils.fucntools import get_client_ip
from utils.values import CreateSubscriptionValues, ProtocolIDs


router = APIRouter()
templates = Jinja2Templates(directory="templates")


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
