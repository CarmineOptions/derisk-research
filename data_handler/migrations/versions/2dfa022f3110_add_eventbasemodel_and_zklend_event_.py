"""Add EventBaseModel and ZkLend event models

Revision ID: 2dfa022f3110
Revises: 64a870953fa5
Create Date: 2024-10-28 18:13:14.699281

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.engine.reflection import Inspector

from shared.constants import ProtocolIDs

revision = "2dfa022f3110"
down_revision = "64a870953fa5"
branch_labels = None
depends_on = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade() -> None:
    """
    Perform the upgrade migration to create the 'event_base_model', 'accumulators_sync_event_data',
    and 'liquidation_event_data' tables if they do not exist.

    This migration creates the following tables:
    - `event_base_model`: Stores general event data with columns for event name, block number, and protocol ID.
    - `accumulators_sync_event_data`: Inherits from the base model and adds specific fields for token and accumulator values.
    - `liquidation_event_data`: Inherits from the base model and adds fields specific to liquidation events.

    Additional configuration:
    - Primary key constraint on the `id` column.
    - Indexes on fields like `event_name`, `block_number`, and `protocol_id` for optimized querying.

    This function is part of the Alembic migration and is auto-generated.
    Adjustments may be made if additional configuration or constraints are needed.
    """

    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    if "event_base_model" not in inspector.get_table_names():
        op.create_table(
            "event_base_model",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                default=sa.text("uuid_generate_v4()"),
            ),
            sa.Column("event_name", sa.String(), nullable=False, index=True),
            sa.Column("block_number", sa.Integer(), nullable=False, index=True),
            sa.Column(
                "protocol_id",
                ENUM(*[e.value for e in ProtocolIDs], name="protocolids"),
                nullable=False,
                index=True,
            ),
        )
        logger.info("Table 'event_base_model' created successfully.")
    else:
        logger.info("Table 'event_base_model' already exists, skipping creation.")

    if "accumulators_sync_event_data" not in inspector.get_table_names():
        op.create_table(
            "accumulators_sync_event_data",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                default=sa.text("uuid_generate_v4()"),
            ),
            sa.Column("event_name", sa.String(), nullable=False, index=True),
            sa.Column("block_number", sa.Integer(), nullable=False, index=True),
            sa.Column(
                "protocol_id",
                ENUM(*[e.value for e in ProtocolIDs], name="protocolids"),
                nullable=False,
                index=True,
            ),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("lending_accumulator", sa.Numeric(38, 18), nullable=False),
            sa.Column("debt_accumulator", sa.Numeric(38, 18), nullable=False),
        )
        logger.info("Table 'accumulators_sync_event_data' created successfully.")
    else:
        logger.info(
            "Table 'accumulators_sync_event_data' already exists, skipping creation."
        )

    if "liquidation_event_data" not in inspector.get_table_names():
        op.create_table(
            "liquidation_event_data",
            sa.Column(
                "id",
                UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                default=sa.text("uuid_generate_v4()"),
            ),
            sa.Column("event_name", sa.String(), nullable=False, index=True),
            sa.Column("block_number", sa.Integer(), nullable=False, index=True),
            sa.Column(
                "protocol_id",
                ENUM(*[e.value for e in ProtocolIDs], name="protocolids"),
                nullable=False,
                index=True,
            ),
            sa.Column("liquidator", sa.String(), nullable=False),
            sa.Column("user", sa.String(), nullable=False),
            sa.Column("debt_token", sa.String(), nullable=False),
            sa.Column("debt_raw_amount", sa.Numeric(38, 18), nullable=False),
            sa.Column("debt_face_amount", sa.Numeric(38, 18), nullable=False),
            sa.Column("collateral_token", sa.String(), nullable=False),
            sa.Column("collateral_amount", sa.Numeric(38, 18), nullable=False),
        )
        logger.info("Table 'liquidation_event_data' created successfully.")
    else:
        logger.info("Table 'liquidation_event_data' already exists, skipping creation.")


def downgrade() -> None:
    """
    Perform the downgrade migration to remove the 'event_base_model', 'accumulators_sync_event_data',
    and 'liquidation_event_data' tables from the database if they exist.

    This migration drops the tables and their associated indexes if they exist, reversing the changes made
    in the `upgrade` function.
    """

    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    if "liquidation_event_data" in inspector.get_table_names():
        op.drop_table("liquidation_event_data")
        logger.info("Table 'liquidation_event_data' dropped successfully.")
    else:
        logger.info("Table 'liquidation_event_data' does not exist, skipping drop.")

    if "accumulators_sync_event_data" in inspector.get_table_names():
        op.drop_table("accumulators_sync_event_data")
        logger.info("Table 'accumulators_sync_event_data' dropped successfully.")
    else:
        logger.info(
            "Table 'accumulators_sync_event_data' does not exist, skipping drop."
        )

    if "event_base_model" in inspector.get_table_names():
        op.drop_table("event_base_model")
        logger.info("Table 'event_base_model' dropped successfully.")
    else:
        logger.info("Table 'event_base_model' does not exist, skipping drop.")
