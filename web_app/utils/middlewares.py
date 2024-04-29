from datetime import datetime

from fastapi import HTTPException, Request, status
from sqlalchemy import func
from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)

from database.database import get_database
from database.models import NotificationData

from .values import MiddlewaresValues


class RateLimitMiddleware(BaseHTTPMiddleware):
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
        current_time_minute = datetime.utcnow().time().minute

        if (
            db.query(NotificationData)
            .filter(
                NotificationData.ip_address == ip_address,
                func.date_part("minute", NotificationData.created_at)
                == current_time_minute,
            )
            .first()
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=MiddlewaresValues.rate_limit_exceeded_message,
            )

        return await call_next(request)
