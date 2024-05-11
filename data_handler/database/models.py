from uuid import uuid4

from sqlalchemy import UUID, BigInteger, Column, Float, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(DeclarativeBase):
    """
    Base class for ORM models.

    :ivar id: The unique identifier of the entity.
    """

    id: Mapped[UUID] = Column(UUID, default=uuid4, primary_key=True)
    metadata = MetaData()


class LoanStates(Base):
    """
    SQLAlchemy model for the loan_states table.
    """

    __tablename__ = "loan_states"

    block = Column(BigInteger, index=True)
    timestamp = Column(BigInteger, index=True)
    protocol = Column(String, index=True)
    user = Column(String, index=True)
    collateral_token = Column(String, index=True)
    collateral_amount = Column(Float)
    debt_token = Column(String, index=True)
    debt_amount = Column(Float)
