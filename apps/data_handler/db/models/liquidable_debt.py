"""SQLAlchemy models for the liquidable debt and health ratio level tables."""

from data_handler.handlers.liquidable_debt.values import LendingProtocolNames
from sqlalchemy import DECIMAL, BigInteger, Column, String
from sqlalchemy_utils.types.choice import ChoiceType

from shared.db.base import Base
from shared.protocol_ids import ProtocolIDs


class LiquidableDebt(Base):
    """
    SQLAlchemy model for the liquidable debt table.
    """

    __tablename__ = "liquidable_debt"
    __table_args__ = {"extend_existing": True}

    liquidable_debt = Column(DECIMAL, nullable=False)
    protocol_name = Column(
        ChoiceType(LendingProtocolNames, impl=String()), nullable=False
    )
    collateral_token_price = Column(DECIMAL, nullable=False)
    collateral_token = Column(String, nullable=False)
    debt_token = Column(String, nullable=False)


class HealthRatioLevel(Base):
    """
    SQLAlchemy model for the health ratio level table.
    """

    __tablename__ = "health_ratio_level"
    __table_args__ = {"extend_existing": True}

    timestamp = Column(BigInteger, index=True)
    user_id = Column(String, index=True)
    value = Column(DECIMAL, nullable=False)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)
