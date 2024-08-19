"""initial migrations

Revision ID: f2c41f4ff53f
Revises: 
Create Date: 2024-05-11 22:00:16.605837

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import sqlalchemy_utils

from utils.values import ProtocolIDs

# revision identifiers, used by Alembic.
revision: str = "f2c41f4ff53f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the current connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if the "notification" table exists before creating it
    if not inspector.has_table("notification"):
        op.create_table(
            "notification",
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("wallet_id", sa.String(), nullable=False),
            sa.Column("telegram_id", sa.String(), nullable=False),
            sa.Column(
                "ip_address",
                sqlalchemy_utils.types.ip_address.IPAddressType(length=50),
                nullable=False,
            ),
            sa.Column("health_ratio_level", sa.Float(), nullable=False),
            sa.Column(
                "protocol_id",
                sqlalchemy_utils.types.choice.ChoiceType(
                    choices=ProtocolIDs, impl=sa.String()
                ),
                nullable=False,
            ),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_notification_email"), "notification", ["email"], unique=True
        )

    # Check if the "telegram_log" table exists before creating it
    if not inspector.has_table("telegram_log"):
        op.create_table(
            "telegram_log",
            sa.Column("sent_at", sa.DateTime(), nullable=False),
            sa.Column("notification_data_id", sa.UUID(), nullable=False),
            sa.Column("is_succesfully", sa.Boolean(), nullable=False),
            sa.Column("message", sa.String(), server_default="", nullable=False),
            sa.Column("id", sa.UUID(), nullable=False),
            sa.ForeignKeyConstraint(
                ["notification_data_id"],
                ["notification.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

def downgrade() -> None:
    # Drop the "telegram_log" table if it exists
    op.drop_table("telegram_log")

    # Drop the index if it exists
    op.drop_index(op.f("ix_notification_email"), table_name="notification")

    # Drop the "notification" table if it exists
    op.drop_table("notification")
