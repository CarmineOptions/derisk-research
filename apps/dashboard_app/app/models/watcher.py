from shared.db import Base
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import IPAddressType
from datetime import datetime
from sqlalchemy_utils.types.choice import ChoiceType
from enum import Enum


class ProtocolIDs(str, Enum):
    HASHSTACK = "Hashstack"
    NOSTRA_ALPHA = "Nostra_alpha"
    NOSTRA_MAINNET = "Nostra_mainnet"
    ZKLEND = "zkLend"


class NotificationData(Base):
    __tablename__ = "notification"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    email: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    wallet_id: Mapped[str] = mapped_column(String, nullable=False)
    telegram_id: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(IPAddressType, nullable=True)
    health_ratio_level: Mapped[float] = mapped_column(Float, nullable=False)
    protocol_id: Mapped[ProtocolIDs] = mapped_column(
        ChoiceType(ProtocolIDs, impl=String()), nullable=False
    )


class TelegramLog(Base):
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    notification_data_id: Mapped[str] = mapped_column(
        ForeignKey(NotificationData.id), nullable=False
    )
    is_succesfully: Mapped[bool] = mapped_column(Boolean, nullable=False)
    message: Mapped[str] = mapped_column(
        String, server_default="", default="", nullable=False
    )
