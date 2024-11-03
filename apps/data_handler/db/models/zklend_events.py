""" This module contains the SQLAlchemy models for the zkLend events. """
from decimal import Decimal

from data_handler.db.models.event import EventBaseModel
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class AccumulatorsSyncEventModel(EventBaseModel):
    """
    Database model for AccumulatorsSync event, inheriting from EventBaseModel.

    This model stores the token address and the converted values for lending and debt
    accumulators as Decimal.
    """

    __tablename__ = "accumulators_sync_event"

    token: Mapped[str] = mapped_column(String, nullable=False)
    lending_accumulator: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    debt_accumulator: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class LiquidationEventModel(EventBaseModel):
    """
    Database model for Liquidation event, inheriting from EventBaseModel.

    This model stores the details of a liquidation event, including addresses and amounts.
    """

    __tablename__ = "liquidation_event"

    liquidator: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    debt_token: Mapped[str] = mapped_column(String, nullable=False)
    debt_raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    debt_face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    collateral_token: Mapped[str] = mapped_column(String, nullable=False)
    collateral_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class RepaymentEventModel(EventBaseModel):
    """
    Database model for Repayment event, inheriting from EventBaseModel.

    This model stores details of a repayment event, including the addresses involved
    and the amounts in raw and face formats.
    """

    __tablename__ = "repayment_event"

    repayer: Mapped[str] = mapped_column(String, nullable=False)
    beneficiary: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class DepositEventModel(EventBaseModel):
    """
    Database model for Deposit event, inheriting from EventBaseModel.

    This model stores details of a deposit event, including the user address,
    token, and the face amount of the deposit.
    """

    __tablename__ = "deposit_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class BorrowingEventModel(EventBaseModel):
    """
    Database model for Borrowing event, inheriting from EventBaseModel.

    This model stores details of a borrowing event, including the user address,
    token, and amounts in raw and face formats.
    """

    __tablename__ = "borrowing_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class WithdrawalEventModel(EventBaseModel):
    """
    Database model for Withdrawal event, inheriting from EventBaseModel.

    This model stores details of a withdrawal event, including the user address,
    token, and the amount withdrawn.
    """

    __tablename__ = "withdrawal_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)


class CollateralEnabledDisabledEventModel(EventBaseModel):
    """
    Database model for CollateralEnabled/Disabled event, inheriting from EventBaseModel.

    This model stores details of a collateral enabled/disabled event, including
    the user address and the token involved.
    """

    __tablename__ = "collateral_enabled_disabled_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
