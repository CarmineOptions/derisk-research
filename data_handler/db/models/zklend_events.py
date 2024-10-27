from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Column, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from data_handler.db.models.event import EventBaseModel


class AccumulatorsSyncEventData(EventBaseModel):
    """
    Database model for AccumulatorsSync event, inheriting from EventBaseModel.

    This model stores the token address and the converted values for lending and debt
    accumulators as Decimal.
    """

    __tablename__ = "accumulators_sync_event_data"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    token: Mapped[str] = mapped_column(String, nullable=False)
    lending_accumulator: Mapped[Decimal] = mapped_column(
        Numeric(38, 18), nullable=False
    )
    debt_accumulator: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "accumulators_sync_event"}


class LiquidationEventData(EventBaseModel):
    """
    Database model for Liquidation event, inheriting from EventBaseModel.

    This model stores the details of a liquidation event, including addresses and amounts.
    """

    __tablename__ = "liquidation_event_data"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    liquidator: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    debt_token: Mapped[str] = mapped_column(String, nullable=False)
    debt_raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    debt_face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    collateral_token: Mapped[str] = mapped_column(String, nullable=False)
    collateral_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "liquidation_event"}
