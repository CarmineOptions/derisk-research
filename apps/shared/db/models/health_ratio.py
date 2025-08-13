from sqlalchemy import DECIMAL, BigInteger, Column, String
from sqlalchemy_utils.types.choice import ChoiceType

from shared.db.base import Base
from shared.protocol_ids import ProtocolIDs


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
