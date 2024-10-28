"""
Module: event.py

Defines the `EventBaseModel` class for storing event data in the database. 
This model includes attributes 
like `event_name`, `block_number`, and `protocol_id`, using the `ProtocolIDs` e
num to enforce valid protocol IDs. 
Fields are indexed for efficient querying.
"""

from sqlalchemy import Column, Enum, Integer, MetaData, String
from sqlalchemy.orm import Mapped, mapped_column

from data_handler.db.models.base import Base
from shared.constants import ProtocolIDs


class EventBaseModel(Base):
    """
    Represents the base model for events in the database. This model stores essential information
    about events
    that occur within the system, including the event's name, the block number it occurred on,
    and the associated protocol.

    Attributes:
    ----------
    event_name : str
    The name of the event. This field is indexed to improve lookup performance
    for event-related queries.
    block_number : int
    The block number in which the event occurred. This field is also indexed to allow
    efficient filtering by block number.
    protocol_id : str
    The protocol identifier associated with the event. This uses an enumeration (Enum)
    to ensure that only valid protocol IDs,
    as defined in the `ProtocolIDs` enum class, are stored. It is indexed to speed up
    queries based on protocol type.
    """

    __tablename__ = "event_base_model"
    
    event_name: Mapped[str] = mapped_column(String, index=True)
    block_number: Mapped[int] = mapped_column(Integer, index=True)
    protocol_id: Mapped[str] = mapped_column(Enum(ProtocolIDs), index=True)
    
    __mapper_args__ = {
        "polymorphic_identity": "event_base",
        "polymorphic_on": type,
    }