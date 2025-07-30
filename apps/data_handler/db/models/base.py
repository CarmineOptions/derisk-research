"""Base classes for ORM models."""

from sqlalchemy import BigInteger, Column, String
from sqlalchemy.types import JSON
from sqlalchemy_utils.types.choice import ChoiceType
from shared.db import Base
from shared.protocol_ids import ProtocolIDs


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
