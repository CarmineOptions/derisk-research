"""add health_ratio_level model

Revision ID: 509baf9251f2
Revises: d271a1dc6633
Create Date: 2024-07-07 14:39:40.075502

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy_utils.types.choice import ChoiceType

from shared.constants import ProtocolIDs

# revision identifiers, used by Alembic.
revision: str = "509baf9251f2"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """ Base class for collectors. """
    # Check if the table already exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if not inspector.has_table("health_ratio_level"):
        # Table does not exist, so create it
        op.create_table(
            "health_ratio_level",
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("value", sa.DECIMAL(), nullable=False),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column(
                "protocol_id",
                ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_health_ratio_level_timestamp"),
            "health_ratio_level",
            ["timestamp"],
            unique=False,
        )
        op.create_index(
            op.f("ix_health_ratio_level_user_id"),
            "health_ratio_level",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    """ Base classes for ORM models. """
    # Drop the indices and table if it exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    if inspector.has_table("health_ratio_level"):
        op.drop_index(op.f("ix_health_ratio_level_user_id"), table_name="health_ratio_level")
        op.drop_index(op.f("ix_health_ratio_level_timestamp"), table_name="health_ratio_level")
        op.drop_table("health_ratio_level")
