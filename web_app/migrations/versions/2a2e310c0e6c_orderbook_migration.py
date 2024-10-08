"""OrderBook migration

Revision ID: 2a2e310c0e6c
Revises: f2c41f4ff53f
Create Date: 2024-05-18 20:54:46.807223

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2a2e310c0e6c"
down_revision: Union[str, None] = "f2c41f4ff53f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "orderbook",
        sa.Column("token_a", sa.String(), nullable=False),
        sa.Column("token_b", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("block", sa.Integer(), nullable=False),
        sa.Column("dex", sa.String(), nullable=False),
        sa.Column("asks", sa.JSON(), nullable=True),
        sa.Column("bids", sa.JSON(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orderbook_dex"), "orderbook", ["dex"], unique=False)
    op.create_index(
        op.f("ix_orderbook_token_a"), "orderbook", ["token_a"], unique=False
    )
    op.create_index(
        op.f("ix_orderbook_token_b"), "orderbook", ["token_b"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_orderbook_token_b"), table_name="orderbook")
    op.drop_index(op.f("ix_orderbook_token_a"), table_name="orderbook")
    op.drop_index(op.f("ix_orderbook_dex"), table_name="orderbook")
    op.drop_table("orderbook")
    # ### end Alembic commands ###
