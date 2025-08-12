from decimal import Decimal

from fastapi import Request

from dashboard_app.app.crud.base import db_connector as dashboard_db_connector
from shared.db.connector import db_connector
from dashboard_app.app.models.watcher import NotificationData

from shared.db.models import HealthRatioLevel
from sqlalchemy import select, desc


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


async def get_all_activated_subscribers_from_db() -> list[NotificationData]:
    """
    Returns all activated subscribers from database
    :return: list[NotificationData]
    """
    return list(
        await dashboard_db_connector.get_all_activated_subscribers(
            model=NotificationData
        )
    )


def calculate_difference(
    a: float | Decimal = None, b: float | Decimal = None
) -> Decimal:
    """
    Calculates difference between two numbers
    """
    a = Decimal(a)
    b = Decimal(b)

    return abs(a - b)


async def get_health_ratio_level_from_endpoint(
    user_id: str, protocol_id: str
) -> Decimal:
    """
    Returns health ratio level from endpoint URL
    :param user_id: str
    :param protocol_id: str
    :return: Decimal
    """
    query = (
        select(HealthRatioLevel)
        .filter(
            HealthRatioLevel.protocol_id == protocol_id,
            HealthRatioLevel.user_id == user_id,
        )
        .order_by(desc(HealthRatioLevel.timestamp))
        .limit(1)
    )
    async with db_connector.session() as session:
        res = await session.execute(query)
    health_ratio = res.scalar_one_or_none()
    if not health_ratio:
        raise ValueError("Health ratio not found")
    return Decimal(health_ratio)
