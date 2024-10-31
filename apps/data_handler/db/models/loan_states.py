""" SQLAlchemy models for the loan_states table. """
from decimal import Decimal

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.types import JSON

from data_handler.db.models.base import Base, BaseState


class LoanState(BaseState):
    """
    SQLAlchemy model for the loan_states table.
    """

    __tablename__ = "loan_state"
    __table_args__ = (
        UniqueConstraint("protocol_id", "user", name="loan_state_protocol_id_user_key"),
    )

    user = Column(String, index=True)
    deposit = Column(JSON, nullable=True)


class InterestRate(BaseState):
    """
    SQLAlchemy model for the interest_rates table.
    """

    __tablename__ = "interest_rate"

    def get_json_deserialized(self) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
        """Deserialize the JSON fields of the model from str to the Decimal type."""
        collateral = {token_name: Decimal(value) for token_name, value in self.collateral.items()}
        debt = {token_name: Decimal(value) for token_name, value in self.debt.items()}
        return collateral, debt


class ZkLendCollateralDebt(Base):
    """
    SQLAlchemy model for table with obligation data for ZkLend.
    """

    __tablename__ = "zklend_collateral_debt"

    user_id = Column(String, nullable=False, index=True)
    collateral = Column(JSON, nullable=True)
    debt = Column(JSON, nullable=True)
    deposit = Column(JSON, nullable=True)
    collateral_enabled = Column(JSON, nullable=False)


class HashtackCollateralDebt(Base):
    """
    SQLAlchemy model for the liquidable debt table for Hashtack.
    """

    __tablename__ = "hashtack_collateral_debt"

    user_id = Column(String, nullable=False, index=True)
    loan_id = Column(Integer, nullable=False)
    collateral = Column(JSON, nullable=True)
    debt = Column(JSON, nullable=True)
    debt_category = Column(Integer, nullable=False)
    original_collateral = Column(JSON, nullable=False)
    borrowed_collateral = Column(JSON, nullable=False)
    version = Column(
        Integer, nullable=False, index=True
    )  # we have two versions of Hashtack V0 and V1
