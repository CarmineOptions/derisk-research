from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID, Column, DateTime, Float, String
from sqlalchemy_utils import IPAddressType

from .database import Base


class NotificationData(Base):
    __tablename__ = "notification"

    id = Column(UUID, default=uuid4(), primary_key=True)
    created_at = Column(DateTime, default=datetime.now())
    email = Column(String, index=True, unique=True, nullable=False)
    wallet_id = Column(String, unique=True, nullable=False)
    telegram_id = Column(String, unique=True, nullable=False)
    ip_address = Column(IPAddressType, unique=True, nullable=False)
    health_ration_level = Column(Float, nullable=False)