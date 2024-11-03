""" SQLAlchemy models for the liquidable debt and health ratio level tables. """
from data_handler.handlers.liquidable_debt.values import LendingProtocolNames
from sqlalchemy import DECIMAL, BigInteger, Column, String
from sqlalchemy_utils.types.choice import ChoiceType

from data_handler.db.models.base import Base
from shared.constants import ProtocolIDs


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


class HealthRatioLevel(Base):
    """
    SQLAlchemy model for the health ratio level table.
    """

    __tablename__ = "health_ratio_level"

    timestamp = Column(BigInteger, index=True)
    user_id = Column(String, index=True)
    value = Column(DECIMAL, nullable=False)
    protocol_id = Column(ChoiceType(ProtocolIDs, impl=String()), nullable=False)
