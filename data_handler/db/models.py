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


class BaseState(Base):
    """
    Base class for state models.
    """
    __abstract__ = True

    block = Column(BigInteger, index=True)
    timestamp = Column(BigInteger, index=True)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)
    collateral = Column(JSON)
    debt = Column(JSON)


class LoanState(BaseState):
    """
    SQLAlchemy model for the loan_states table.
    """

    __tablename__ = "loan_state"
    user = Column(String, index=True)
    deposit = Column(JSON, nullable=True)


class InterestRate(BaseState):
    """
    SQLAlchemy model for the interest_rates table.
    """

    __tablename__ = "interest_rate"


class LiquidableDebt(Base):
    """
    SQLAlchemy model for the liquidable debt table.
    """

    __tablename__ = "liquidable_debt"

    liquidable_debt = Column(DECIMAL, nullable=False)
    protocol_name = Column(ChoiceType(LendingProtocolNames, impl=String()), nullable=False)
    collateral_token_price = Column(DECIMAL, nullable=False)
    collateral_token = Column(String, nullable=False)
    debt_token = Column(String, nullable=False)


class OrderBookModel(Base):
    """
    Represents an order book entry in the database.
    """
    __tablename__ = "orderbook"

    token_a = Column(String, nullable=False, index=True)
    token_b = Column(String, nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False)
    block = Column(BigInteger, nullable=False)
    dex = Column(String, nullable=False, index=True)
    asks = Column(JSON, nullable=True)
    bids = Column(JSON, nullable=True)
