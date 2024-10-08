import time
from decimal import Decimal

import requests
from database.crud import DBConnector
from database.models import NotificationData
from fastapi import Request
from utils.values import HEALTH_RATIO_URL


def get_client_ip(request: Request) -> str:
    """
    Returns the client IP address
    :param request: Request
    :return: str
    """
    x_forwarded_for = request.headers.get("x-forwarded-for", "")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.client.host

    return ip


def get_all_activated_subscribers_from_db() -> list[NotificationData]:
    """
    Returns all activated subscribers from database
    :return: list[NotificationData]
    """
    return list(DBConnector().get_all_activated_subscribers(model=NotificationData))


def calculate_difference(
    a: float | Decimal = None, b: float | Decimal = None
) -> Decimal:
    """
    Calculates difference between two numbers
    """
    a = Decimal(a)
    b = Decimal(b)

    return abs(a - b)


def get_health_ratio_level_from_endpoint(user_id: str, protocol_id: str) -> Decimal:
    """
    Returns health ratio level from endpoint URL
    :param user_id: str
    :param protocol_id: str
    :return: Decimal
    """
    url = HEALTH_RATIO_URL.format(protocol=protocol_id, user_id=user_id)

    try:
        response = requests.get(url)
        response.raise_for_status()

        return Decimal(response.text)

    except Exception:
        time.sleep(10)

        response = requests.get(url)
        response.raise_for_status()

        return Decimal(response.text)
