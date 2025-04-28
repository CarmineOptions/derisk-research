from typing import Optional
from pydantic import BaseModel, EmailStr
from pydantic.networks import IPvAnyAddress
from app.utils.values import ProtocolIDs

class NotificationForm(BaseModel):
    """
    Serializer for notification subscription payload.
    """
    email: Optional[EmailStr] = None
    wallet_id: str
    telegram_id: Optional[str] = None
    ip_address: Optional[IPvAnyAddress] = None
    health_ratio_level: float
    protocol_id: ProtocolIDs 
