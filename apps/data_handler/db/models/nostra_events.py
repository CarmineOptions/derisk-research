from decimal import Decimal

from data_handler.db.models.event import EventBaseModel
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column


class BearingCollateralBurnEventModel(EventBaseModel):
    """
    Database model for BearingCollateralBurn event, inheriting from EventBaseModel.

    This model stores the user address and the amount burned.
    """

    __tablename__ = "bearing_collateral_burn_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class BearingCollateralMintEventModel(EventBaseModel):
    """
    Database model for BearingCollateral mint event, inheriting from EventBaseModel.

    This model stores the user address and the amount minted.
    """

    __tablename__ = "bearing_collateral_mint_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


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


class DebtTransferEventModel(EventBaseModel):
    """
    Database model for DebtTransfer event, inheriting from EventBaseModel.

    This model stores the sender address, recipient address, and the transfer amount.
    """

    __tablename__ = "debt_transfer_event"

    sender: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class InterestRateModelEventModel(EventBaseModel):
    """
    Database model for InterestRate event, inheriting from EventBaseModel.

    This model stores the
        debt_token (str): The address of the debt token.
        lending_index (Decimal): The lending index in hexadecimal.
        borrow_index (Decimal): The borrow index in hexadecimal.
    """

    __tablename__ = "interest_rate_event"

    debt_token: Mapped[str] = mapped_column(String, nullable=False)
    lending_index: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    borrow_index: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class NonInterestBearingCollateralMintEventModel(EventBaseModel):
    """
    Database model for NonInterestBearingCollateralMint event.
    """

    __tablename__ = "non_interest_bearing_collateral_mint_event"

    sender: Mapped[str] = mapped_column(String, nullable=False)
    recipient: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)


class NonInterestBearingCollateralBurnEventModel(EventBaseModel):
    """
    Database model for NonInterestBearingCollateralBurn event.
    """

    __tablename__ = "non_interest_bearing_collateral_burn_event"

    user: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
