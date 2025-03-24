from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import uuid4, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy import Column, MetaData

class Base(DeclarativeBase):
    id: Mapped[UUID] = Column(PG_UUID(as_uuid=True), default=uuid4, primary_key=True)
    metadata = MetaData()