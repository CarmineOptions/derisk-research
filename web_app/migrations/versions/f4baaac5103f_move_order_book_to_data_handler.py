"""move order book to data handler

Revision ID: f4baaac5103f
Revises: a9d6a1c36e33
Create Date: 2024-05-31 20:50:59.098432

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f4baaac5103f"
down_revision: Union[str, None] = "a9d6a1c36e33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_orderbook_dex", table_name="orderbook")
    op.drop_index("ix_orderbook_token_a", table_name="orderbook")
    op.drop_index("ix_orderbook_token_b", table_name="orderbook")
    op.drop_table("orderbook")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "orderbook",
        sa.Column("token_a", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("token_b", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("timestamp", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("block", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("dex", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "asks",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "bids",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="orderbook_pkey"),
    )
    op.create_index("ix_orderbook_token_b", "orderbook", ["token_b"], unique=False)
    op.create_index("ix_orderbook_token_a", "orderbook", ["token_a"], unique=False)
    op.create_index("ix_orderbook_dex", "orderbook", ["dex"], unique=False)
    # ### end Alembic commands ###
