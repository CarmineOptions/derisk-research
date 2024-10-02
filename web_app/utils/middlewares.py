import os
from datetime import datetime

import httpx
from database.database import get_database
from database.models import NotificationData
from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)

from .values import MiddlewaresValues

load_dotenv()

TOKEN = os.environ.get("IP_INFO_TOKEN", "")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks if user has exceeded the rate limit.
    It also checks if the IP address has access to our API

    Validations:
        - IP address validation
        - Rate limit validation
    """

    async def dispatch(
        self, request: Request = None, call_next: RequestResponseEndpoint = None
    ) -> RequestResponseEndpoint:
        """
        Check's if rate limit is exceeded.
        :param request: Request
        :param call_next: RequestResponseEndpoint
        :return: RequestResponseEndpoint
        """
        db = next(get_database())
        ip_address = request.client.host
        current_time = datetime.utcnow().time()

        await self.check_country_access(ip_address)

        if self.has_exceeded_rate_limit_per_minute(
            db=db, ip_address=ip_address, current_time_minute=current_time.minute
        ):
            if self.has_exceeded_rate_limit_per_hour(
                db=db, ip_address=ip_address, current_time_hour=current_time.hour
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=MiddlewaresValues.rate_limit_exceeded_message,
                )

        return await call_next(request)

    @classmethod
    def has_exceeded_rate_limit_per_hour(
        cls, db: Session = None, ip_address: str = None, current_time_hour: int = None
    ) -> bool:
        """
        Check's if rate limit per minute is exceeded
        :param db: Session = None
        :param ip_address: str = None
        :param current_time_hour: int = None
        :return: bool
        """
        return (
            len(
                db.query(NotificationData).filter(
                    NotificationData.ip_address == ip_address,
                    func.date_part("hour", NotificationData.created_at)
                    == current_time_hour,
                )
            )
            >= MiddlewaresValues.requests_per_hour_limit
        )

    @classmethod
    def has_exceeded_rate_limit_per_minute(
        cls, db: Session = None, ip_address: str = None, current_time_minute: int = None
    ) -> bool:
        """
        Check's if rate limit per minute is exceeded
        :param db: Session = None
        :param ip_address: str = None
        :param current_time_minute: int = None
        :return: bool
        """
        return (
            len(
                db.query(NotificationData).filter(
                    NotificationData.ip_address == ip_address,
                    func.date_part("minute", NotificationData.created_at)
                    == current_time_minute,
                )
            )
            >= MiddlewaresValues.requests_per_minute_limit
        )

    @classmethod
    async def check_country_access(cls, ip_address: str = None) -> None:
        """
        Check's if country is not in black list
        :param ip_address: str = None
        :return: None
        """

        if (
            await cls._get_country_by_ip(ip_address)
            in MiddlewaresValues.denied_access_countries
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MiddlewaresValues.country_access_denied_message,
            )

    @classmethod
    async def _get_country_by_ip(cls, ip: str = None) -> str:
        """
        Returns country by ip
        :param ip: str = None
        :return: str
        """
        url = f"https://ipinfo.io/{ip}/json?token={TOKEN}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

            return data.get("country", "")
