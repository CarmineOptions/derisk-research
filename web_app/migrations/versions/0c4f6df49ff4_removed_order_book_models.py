"""removed order book models'


Revision ID: 0c4f6df49ff4
Revises: f4baaac5103f
Create Date: 2024-08-15 08:52:04.029928

"""

from typing import Sequence, Union
from sqlalchemy.dialects import postgresql
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "0c4f6df49ff4"
down_revision: Union[str, None] = "f4baaac5103f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check and drop ix_loan_state_block if it exists
    if 'ix_loan_state_block' in [index['name'] for index in inspector.get_indexes('loan_state')]:
        op.drop_index("ix_loan_state_block", table_name="loan_state")

    # Check and drop ix_loan_state_timestamp if it exists
    if 'ix_loan_state_timestamp' in [index['name'] for index in inspector.get_indexes('loan_state')]:
        op.drop_index("ix_loan_state_timestamp", table_name="loan_state")

    # Check and drop ix_loan_state_user if it exists
    if 'ix_loan_state_user' in [index['name'] for index in inspector.get_indexes('loan_state')]:
        op.drop_index("ix_loan_state_user", table_name="loan_state")

    op.drop_table("loan_state")

    # Check and drop ix_liquidable_debt_user if it exists
    if 'ix_liquidable_debt_user' in [index['name'] for index in inspector.get_indexes('liquidable_debt')]:
        op.drop_index("ix_liquidable_debt_user", table_name="liquidable_debt")

    op.drop_table("liquidable_debt")


def downgrade() -> None:
    # The downgrade function remains the same
    op.create_table(
        "liquidable_debt",
        sa.Column(
            "protocol", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.Column("user", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "computed_debt",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="liquidable_debt_pkey"),
    )
    op.create_index(
        "ix_liquidable_debt_user", "liquidable_debt", ["user"], unique=False
    )
    op.create_table(
        "loan_state",
        sa.Column("block", sa.BIGINT(), autoincrement=False, nullable=True),
        sa.Column(
            "timestamp", sa.BIGINT(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "protocol_id", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.Column("user", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "collateral",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "debt",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="loan_state_pkey"),
    )
    op.create_index("ix_loan_state_user", "loan_state", ["user"], unique=False)
    op.create_index(
        "ix_loan_state_timestamp", "loan_state", ["timestamp"], unique=False
    )
    op.create_index(
        "ix_loan_state_block", "loan_state", ["block"], unique=False
    )