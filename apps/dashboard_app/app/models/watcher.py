from base import Base

class NotificationData(Base):
    __tablename__ = "notification"

    created_at = Column(DateTime, default=datetime.now())
    email = Column(String, index=True, nullable=True)
    wallet_id = Column(String, nullable=False)
    telegram_id = Column(String, unique=False, nullable=False)
    ip_address = Column(IPAddressType, nullable=True)
    health_ratio_level = Column(Float, nullable=False)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)


class TelegramLog(Base):
    """
    Represents a log entry for Telegram notifications.

    :ivar sent_at: The timestamp indicating when the message was sent.
    :ivar notification_data_id: The UUID identifying the notification data associated with this log entry.
    :ivar is_succesfully: A boolean indicating whether the message was sent successfully or not.
    :ivar message: The content of the send message being logged.
    """

    __tablename__ = "telegram_log"

    sent_at = Column(DateTime, default=datetime.now(), nullable=False)
    notification_data_id = Column(ForeignKey(NotificationData.id), nullable=False)
    is_succesfully = Column(Boolean, nullable=False)
    message = Column(String, server_default="", default="", nullable=False)