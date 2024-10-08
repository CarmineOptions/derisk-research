from decimal import Decimal
from uuid import uuid4

from handler_tools.constants import ProtocolIDs
from handlers.liquidable_debt.values import LendingProtocolNames
from sqlalchemy import DECIMAL, UUID, BigInteger, Column, Integer, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.types import JSON
from sqlalchemy_utils.types.choice import ChoiceType


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

    def get_json_deserialized(self) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
        """Deserialize the JSON fields of the model from str to the Decimal type."""
        collateral = {
            token_name: Decimal(value) for token_name, value in self.collateral.items()
        }
        debt = {token_name: Decimal(value) for token_name, value in self.debt.items()}
        return collateral, debt


class LiquidableDebt(Base):
    """
    SQLAlchemy model for the liquidable debt table.
    """

    __tablename__ = "liquidable_debt"

    liquidable_debt = Column(DECIMAL, nullable=False)
    protocol_name = Column(
        ChoiceType(LendingProtocolNames, impl=String()), nullable=False
    )
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
    current_price = Column(DECIMAL, nullable=True)
    asks = Column(JSON, nullable=True)
    bids = Column(JSON, nullable=True)


class HealthRatioLevel(Base):
    """
    SQLAlchemy model for the health ratio level table.
    """

    __tablename__ = "health_ratio_level"

    timestamp = Column(BigInteger, index=True)
    user_id = Column(String, index=True)
    value = Column(DECIMAL, nullable=False)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)


class ZkLendCollateralDebt(Base):
    """
    SQLAlchemy model for table with obligation data for ZkLend.
    """

    __tablename__ = "zklend_collateral_debt"

    user_id = Column(String, nullable=False, index=True)
    collateral = Column(JSON, nullable=True)
    debt = Column(JSON, nullable=True)
    deposit = Column(JSON, nullable=True)
    collateral_enabled = Column(JSON, nullable=False)


class HashtackCollateralDebt(Base):
    """
    SQLAlchemy model for the liquidable debt table for Hashtack.
    """

    __tablename__ = "hashtack_collateral_debt"

    user_id = Column(String, nullable=False, index=True)
    loan_id = Column(Integer, nullable=False)
    collateral = Column(JSON, nullable=True)
    debt = Column(JSON, nullable=True)
    debt_category = Column(Integer, nullable=False)
    original_collateral = Column(JSON, nullable=False)
    borrowed_collateral = Column(JSON, nullable=False)
    version = Column(
        Integer, nullable=False, index=True
    )  # we have two versions of Hashtack V0 and V1
