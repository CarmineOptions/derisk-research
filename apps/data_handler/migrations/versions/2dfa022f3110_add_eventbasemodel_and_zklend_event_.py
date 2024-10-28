def upgrade() -> None:
    """
    Perform the upgrade migration to create the 'accumulators_sync_event_data'
    and 'liquidation_event_data' tables, inheriting fields from the abstract base model.

    This migration creates the following tables:
    - `accumulators_sync_event_data`: Inherits from the base model and adds specific fields for token and accumulator values.
    - `liquidation_event_data`: Inherits from the base model and adds fields specific to liquidation events.

    Additional configuration:
    - Primary key constraint on the `id` column.
    - Indexes on fields like `event_name`, `block_number`, and `protocol_id` for optimized querying.

    Note: `event_base_model` is treated as an abstract base model and is not created as a table.
    """

    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    # Create accumulators_sync_event_data table
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
        logger.info("Table 'accumulators_sync_event_data' already exists, skipping creation.")

    # Create liquidation_event_data table
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
