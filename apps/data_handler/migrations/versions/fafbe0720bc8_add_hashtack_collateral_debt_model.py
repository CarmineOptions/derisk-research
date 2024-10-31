"""add hashtack collateral debt model

Revision ID: fafbe0720bc8
Revises: 70353336c9ef
Create Date: 2024-08-07 10:31:47.338655

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "fafbe0720bc8"
down_revision: Union[str, None] = "70353336c9ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates the 'hashtack_collateral_debt' table if it does not exist."""
    # Check if the table already exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if not inspector.has_table("hashtack_collateral_debt"):
        # Table does not exist, so create it
        op.create_table(
            "hashtack_collateral_debt",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("loan_id", sa.Integer(), nullable=False),
            sa.Column("collateral", sa.JSON(), nullable=True),
            sa.Column("debt", sa.JSON(), nullable=True),
            sa.Column("debt_category", sa.Integer(), nullable=False),
            sa.Column("original_collateral", sa.JSON(), nullable=False),
            sa.Column("borrowed_collateral", sa.JSON(), nullable=False),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_hashtack_collateral_debt_user_id"),
            "hashtack_collateral_debt",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    """Drops the 'hashtack_collateral_debt' table."""
    # Drop the index and table if it exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if inspector.has_table("hashtack_collateral_debt"):
        op.drop_index(
            op.f("ix_hashtack_collateral_debt_user_id"),
            table_name="hashtack_collateral_debt",
        )
        op.drop_table("hashtack_collateral_debt")
