from uuid import uuid4

from sqlalchemy import UUID, Column, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(DeclarativeBase):
    """
    Base class for ORM models.

    :ivar id: The unique identifier of the entity.
    """

    id: Mapped[UUID] = Column(UUID, default=uuid4, primary_key=True)
    metadata = MetaData()
