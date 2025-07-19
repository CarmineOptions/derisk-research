from typing import Optional
from dashboard_app.app.models.watcher import ProtocolIDs
from pydantic import BaseModel, EmailStr
from pydantic.networks import IPvAnyAddress


class NotificationForm(BaseModel):
    """
    Serializer for notification subscription payload.
    """

    email: Optional[EmailStr] = None
    wallet_id: str
    telegram_id: Optional[str] = None
    health_ratio_level: float
    protocol_id: ProtocolIDs
