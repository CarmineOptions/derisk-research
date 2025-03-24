from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, MetaData
from uuid import uuid4, UUID
from sqlalchemy.orm import Mapped


class Base(DeclarativeBase):
    """
    Base class for ORM models.

    :ivar id: The unique identifier of the entity.
    """

    id: Mapped[UUID] = Column(UUID, default=uuid4, primary_key=True)
    metadata = MetaData()