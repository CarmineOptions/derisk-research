"""add new event models

Revision ID: aecc94d73ee6
Revises: 71a8b872296d
Create Date: 2024-10-31 12:19:17.551380

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from shared.constants import ProtocolIDs

# revision identifiers, used by Alembic.
revision: str = "aecc94d73ee6"
down_revision: Union[str, None] = "71a8b872296d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """ Upgrade the database """

    conn = op.get_bind()

    if not conn.engine.dialect.has_table(conn, "borrowing_event"):
        op.create_table(
            "borrowing_event",
            sa.Column("user", sa.String(), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("raw_amount", sa.Numeric(precision=38, scale=18), nullable=False),
            sa.Column(
                "face_amount", sa.Numeric(precision=38, scale=18), nullable=False
            ),
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=False),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_borrowing_event_block_number"),
            "borrowing_event",
            ["block_number"],
            unique=False,
        )
        op.create_index(
            op.f("ix_borrowing_event_name"),
            "borrowing_event",
            ["event_name"],
            unique=False,
        )

    if not conn.engine.dialect.has_table(conn, "collateral_enabled_disabled_event"):
        op.create_table(
            "collateral_enabled_disabled_event",
            sa.Column("user", sa.String(), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=False),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_collateral_enabled_disabled_event_block_number"),
            "collateral_enabled_disabled_event",
            ["block_number"],
            unique=False,
        )
        op.create_index(
            op.f("ix_collateral_enabled_disabled_event_name"),
            "collateral_enabled_disabled_event",
            ["event_name"],
            unique=False,
        )

    if not conn.engine.dialect.has_table(conn, "deposit_event"):
        op.create_table(
            "deposit_event",
            sa.Column("user", sa.String(), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column(
                "face_amount", sa.Numeric(precision=38, scale=18), nullable=False
            ),
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=False),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_deposit_event_block_number"),
            "deposit_event",
            ["block_number"],
            unique=False,
        )
        op.create_index(
            op.f("ix_deposit_event_name"),
            "deposit_event",
            ["event_name"],
            unique=False,
        )

    if not conn.engine.dialect.has_table(conn, "repayment_event"):

        op.create_table(
            "repayment_event",
            sa.Column("repayer", sa.String(), nullable=False),
            sa.Column("beneficiary", sa.String(), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("raw_amount", sa.Numeric(precision=38, scale=18), nullable=False),
            sa.Column(
                "face_amount", sa.Numeric(precision=38, scale=18), nullable=False
            ),
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=False),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_repayment_event_block_number"),
            "repayment_event",
            ["block_number"],
            unique=False,
        )
        op.create_index(
            op.f("ix_repayment_event_name"),
            "repayment_event",
            ["event_name"],
            unique=False,
        )

    if not conn.engine.dialect.has_table(conn, "withdrawal_event"):
        op.create_table(
            "withdrawal_event",
            sa.Column("user", sa.String(), nullable=False),
            sa.Column("amount", sa.Numeric(precision=38, scale=18), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("event_name", sa.String(), nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=False),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs),
                nullable=False,
            ),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_withdrawal_event_block_number"),
            "withdrawal_event",
            ["block_number"],
            unique=False,
        )
        op.create_index(
            op.f("ix_withdrawal_event_name"),
            "withdrawal_event",
            ["event_name"],
            unique=False,
        )


def downgrade() -> None:
    """ Downgrade the database """
    conn = op.get_bind()

    if conn.engine.dialect.has_table(conn, "withdrawal_event"):
        op.drop_index(op.f("ix_withdrawal_event_name"), table_name="withdrawal_event")
        op.drop_index(
            op.f("ix_withdrawal_event_block_number"), table_name="withdrawal_event"
        )
        op.drop_table("withdrawal_event")

    if conn.engine.dialect.has_table(conn, "repayment_event"):
        op.drop_index(op.f("ix_repayment_event_name"), table_name="repayment_event")
        op.drop_index(
            op.f("ix_repayment_event_block_number"), table_name="repayment_event"
        )
        op.drop_table("repayment_event")

    if conn.engine.dialect.has_table(conn, "deposit_event"):
        op.drop_index(op.f("ix_deposit_event_name"), table_name="deposit_event")
        op.drop_index(op.f("ix_deposit_event_block_number"), table_name="deposit_event")
        op.drop_table("deposit_event")

    if conn.engine.dialect.has_table(conn, "collateral_enabled_disabled_event"):
        op.drop_index(
            op.f("ix_collateral_enabled_disabled_event_name"),
            table_name="collateral_enabled_disabled_event",
        )
        op.drop_index(
            op.f("ix_collateral_enabled_disabled_event_block_number"),
            table_name="collateral_enabled_disabled_event",
        )
        op.drop_table("collateral_enabled_disabled_event")

    if conn.engine.dialect.has_table(conn, "borrowing_event"):
        op.drop_index(op.f("ix_borrowing_event_name"), table_name="borrowing_event")
        op.drop_index(
            op.f("ix_borrowing_event_block_number"), table_name="borrowing_event"
        )
        op.drop_table("borrowing_event")