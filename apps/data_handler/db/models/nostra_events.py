from decimal import Decimal
from data_handler.db.models.event import EventBaseModel
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class DebtMintEventModel(EventBaseModel):
    """
    Database model for DebtMint event, inheriting from EventBaseModel.

    This model stores the user address and the amount minted.
    """

    __tablename__ = "debt_mint_event"
from decimal import Decimal
from data_handler.db.models.event import EventBaseModel
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class DebtMintEventModel(EventBaseModel):
    """
    Database model for DebtMint event, inheriting from EventBaseModel.

    This model stores the user address and the amount minted.
    """

    __tablename__ = "debt_mint_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class DebtBurnEventModel(EventBaseModel):
    """
    Database model for DebtBurn event, inheriting from EventBaseModel.

    This model stores the user address and the amount burned.
    """

    __tablename__ = "debt_burn_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class BearingCollateralBurnEventModel(EventBaseModel):
    """
    Database model for BearingCollateralBurn event, inheriting from EventBaseModel.

    This model stores the user address and the amount burned.
    """

    __tablename__ = "bearing_collateral_burn_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class DebtTransferEventModel(EventBaseModel):
    """
    Database model for DebtTransfer event, inheriting from EventBaseModel.

    This model stores the sender address, recipient address, and the transfer amount.
    """

    __tablename__ = "debt_transfer_event"

    sender: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class DebtBurnEventModel(EventBaseModel):
    """
    Database model for DebtBurn event, inheriting from EventBaseModel.

    This model stores the user address and the amount burned.
    """

    __tablename__ = "debt_burn_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
