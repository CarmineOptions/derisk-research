""" This module contains the OrderBookModel class representing 
an order book entry in the database. """
from sqlalchemy import DECIMAL, BigInteger, Column, String
from sqlalchemy.types import JSON

from data_handler.db.models.base import Base


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
