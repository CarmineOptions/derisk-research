from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from data_handler.db.models.event import EventBaseModel


class AccumulatorsSyncEventData(EventBaseModel):
    """
    Database model for AccumulatorsSync event, inheriting from EventBaseModel.

    This model stores the token address and the converted values for lending and debt
    accumulators as Decimal.
    """

    __tablename__ = "accumulators_sync_event_data"

    token: Mapped[str] = mapped_column(String, nullable=False)
    lending_accumulator: Mapped[Decimal] = mapped_column(
        Numeric(38, 18), nullable=False
    )
    debt_accumulator: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class LiquidationEventData(EventBaseModel):
    """
    Database model for Liquidation event, inheriting from EventBaseModel.

    This model stores the details of a liquidation event, including addresses and amounts.
    """

    __tablename__ = "liquidation_event_data"

    liquidator: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    debt_token: Mapped[str] = mapped_column(String, nullable=False)
    debt_raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    debt_face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    collateral_token: Mapped[str] = mapped_column(String, nullable=False)
    collateral_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class RepaymentEventData(EventBaseModel):
    """
    Database model for Repayment event, inheriting from EventBaseModel.

    This model stores details of a repayment event, including the addresses involved
    and the amounts in raw and face formats.
    """

    __tablename__ = "repayment_event_data"

    repayer: Mapped[str] = mapped_column(String, nullable=False)
    beneficiary: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class DepositEventData(EventBaseModel):
    """
    Database model for Deposit event, inheriting from EventBaseModel.

    This model stores details of a deposit event, including the user address,
    token, and the face amount of the deposit.
    """

    __tablename__ = "deposit_event_data"

    user: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class BorrowingEventData(EventBaseModel):
    """
    Database model for Borrowing event, inheriting from EventBaseModel.

    This model stores details of a borrowing event, including the user address,
    token, and amounts in raw and face formats.
    """

    __tablename__ = "borrowing_event_data"

    user: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
    raw_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    face_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class WithdrawalEventData(EventBaseModel):
    """
    Database model for Withdrawal event, inheriting from EventBaseModel.

    This model stores details of a withdrawal event, including the user address,
    token, and the amount withdrawn.
    """

    __tablename__ = "withdrawal_event_data"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)


class CollateralEnabledDisabledEventData(EventBaseModel):
    """
    Database model for CollateralEnabled/Disabled event, inheriting from EventBaseModel.

    This model stores details of a collateral enabled/disabled event, including
    the user address and the token involved.
    """

    __tablename__ = "collateral_enabled_disabled_event_data"

    user: Mapped[str] = mapped_column(String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False)
