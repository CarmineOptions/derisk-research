from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer, UUID, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(DeclarativeBase):
    """
    Base class for ORM models.
    :ivar id: The unique identifier of the entity.
    """

    id: Mapped[UUID] = Column(UUID, default=uuid4, primary_key=True)


class User(Base):
    """
    Represents a user in the system.

    :ivar wallet_id: Optional unique wallet identifier.
    :ivar email: Optional unique email address.
    :ivar token: Required authentication token.
    :ivar created_at: Timestamp of when the user was created.
    :ivar updated_at: Timestamp of the last update to the user record.
    :ivar request_number: Counter for number of requests made.
    """

    __tablename__ = "user"

    wallet_id = Column(String, unique=True, nullable=True, index=True)
    email = Column(String, unique=True, nullable=True, index=True)
    token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    request_number = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, wallet_id={self.wallet_id})>"
