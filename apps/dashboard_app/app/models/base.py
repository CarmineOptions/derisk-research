from re import sub
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import uuid4, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr
from sqlalchemy import Column, MetaData


class Base(DeclarativeBase):
    id: Mapped[UUID] = Column(PG_UUID(as_uuid=True), default=uuid4, primary_key=True)
    metadata = MetaData()

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
