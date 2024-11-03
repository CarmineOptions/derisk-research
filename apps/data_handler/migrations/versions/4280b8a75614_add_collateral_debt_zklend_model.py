"""add collateral debt zklend model

Revision ID: 4280b8a75614
Revises: 31430d42d46a
Create Date: 2024-07-31 09:20:15.371773

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "4280b8a75614"
down_revision: Union[str, None] = "31430d42d46a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """ Base class for collectors. """
    # Check if the table already exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if not inspector.has_table("zklend_collateral_debt"):
        # Table does not exist, so create it
        op.create_table(
            "zklend_collateral_debt",
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("collateral", sa.JSON(), nullable=True),
            sa.Column("debt", sa.JSON(), nullable=True),
            sa.Column("deposit", sa.JSON(), nullable=True),
            sa.Column("collateral_enabled", sa.JSON(), nullable=False),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_zklend_collateral_debt_user_id"),
            "zklend_collateral_debt",
            ["user_id"],
            unique=False,
        )

    # The column drop should only happen if the column exists
    if inspector.has_table("liquidable_debt"):
        columns = [col["name"] for col in inspector.get_columns("liquidable_debt")]
        if "price" in columns:
            op.drop_column("liquidable_debt", "price")


def downgrade() -> None:
    """ Base classes for ORM models. """
    # Drop the index and table if it exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if inspector.has_table("zklend_collateral_debt"):
        op.drop_index(
            op.f("ix_zklend_collateral_debt_user_id"),
            table_name="zklend_collateral_debt",
        )
        op.drop_table("zklend_collateral_debt")
