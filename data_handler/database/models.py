from uuid import uuid4

from sqlalchemy import UUID, BigInteger, Column, MetaData, String, DECIMAL
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.types import JSON
from sqlalchemy_utils.types.choice import ChoiceType

from tools.constants import ProtocolIDs
from handlers.liquidable_debt.values import LendingProtocolNames

class Base(DeclarativeBase):
    """
    Base class for ORM models.

    :ivar id: The unique identifier of the entity.
    """

    id: Mapped[UUID] = Column(UUID, default=uuid4, primary_key=True)
    metadata = MetaData()


class LoanState(Base):
    """
    SQLAlchemy model for the loan_states table.
    """

    __tablename__ = "loan_state"

    block = Column(BigInteger, index=True)
    timestamp = Column(BigInteger, index=True)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)
    user = Column(String, index=True)
    collateral = Column(JSON)
    debt = Column(JSON)
    deposit = Column(JSON, nullable=True)


class LiquidableDebt(Base):
    """
    SQLAlchemy model for the liquidable debt table.
    """

    __tablename__ = "liquidable_debt"

    liquidable_debt = Column(DECIMAL, nullable=False)
    protocol = Column(ChoiceType(LendingProtocolNames, impl=String()), nullable=False)
    price = Column(DECIMAL, nullable=False)
    collateral_token = Column(String, nullable=False)
    debt_token = Column(String, nullable=False)
