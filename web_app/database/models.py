from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, Float, String
from sqlalchemy_utils import IPAddressType
from sqlalchemy_utils.types.choice import ChoiceType

from utils.values import ProtocolIDs

from .database import Base


class NotificationData(Base):
    __tablename__ = "notification"

    id = Column(UUID, default=uuid4, primary_key=True)
    created_at = Column(DateTime, default=datetime.now())
    email = Column(String, index=True, unique=True, nullable=False)
    wallet_id = Column(String, nullable=False)
    telegram_id = Column(String, unique=True, nullable=False)
    ip_address = Column(IPAddressType, nullable=False)
    health_ratio_level = Column(Float, nullable=False)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)
