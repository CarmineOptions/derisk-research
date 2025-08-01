"""Add LoanState model

Revision ID: d2fa8201b04a
Revises: aa0d88b79e4b
Create Date: 2024-05-13 21:07:50.245027

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

from shared.protocol_ids import ProtocolIDs

# revision identifiers, used by Alembic.
revision: str = "d2fa8201b04a"
down_revision: Union[str, None] = "aa0d88b79e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Base classes for ORM models."""
    # Check if the table 'loan_state' already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "loan_state" not in inspector.get_table_names():
        ### commands auto generated by Alembic - please adjust! ###
        op.create_table(
            "loan_state",
            sa.Column("block", sa.BigInteger(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.Column("user", sa.String(), nullable=True),
            sa.Column("collateral", sa.JSON(), nullable=True),
            sa.Column("debt", sa.JSON(), nullable=True),
            sa.Column("deposit", sa.JSON(), nullable=True),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_loan_state_block"), "loan_state", ["block"], unique=False
        )
        op.create_index(
            op.f("ix_loan_state_timestamp"), "loan_state", ["timestamp"], unique=False
        )
        op.create_index(
            op.f("ix_loan_state_user"), "loan_state", ["user"], unique=False
        )
        ### end Alembic commands ###
    else:
        print("Table 'loan_state' already exists, skipping creation.")


def downgrade() -> None:
    """Base classes for ORM models."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_loan_state_user"), table_name="loan_state")
    op.drop_index(op.f("ix_loan_state_timestamp"), table_name="loan_state")
    op.drop_index(op.f("ix_loan_state_block"), table_name="loan_state")
    op.drop_table("loan_state")
    # ### end Alembic commands ###
