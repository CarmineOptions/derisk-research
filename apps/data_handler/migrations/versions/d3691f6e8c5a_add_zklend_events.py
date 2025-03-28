"""add zklend events

Revision ID: d3691f6e8c5a
Revises: 64a870953fa5
Create Date: 2024-11-01 10:53:33.024930

This migration adds the necessary tables and relationships for tracking ZkLend events
in the system, including event tracking, transaction details and related metadata.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from apps.shared.constants import ProtocolIDs


# revision identifiers, used by Alembic.
revision: str = 'd3691f6e8c5a'
down_revision: Union[str, None] = '64a870953fa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade the database schema to include ZkLend events.
    
    Creates new tables and relationships required for storing ZkLend event data,
    including:
    - Event tracking
    - Transaction details 
    - Related metadata
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('accumulators_sync_event',
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('lending_accumulator', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('debt_accumulator', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accumulators_sync_event_block_number'), 'accumulators_sync_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_accumulators_sync_event_event_name'), 'accumulators_sync_event', ['event_name'], unique=False)
    op.create_table('borrowing_event',
    sa.Column('user', sa.String(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('raw_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('face_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_borrowing_event_block_number'), 'borrowing_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_borrowing_event_event_name'), 'borrowing_event', ['event_name'], unique=False)
    op.create_table('collateral_enabled_disabled_event',
    sa.Column('user', sa.String(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_collateral_enabled_disabled_event_block_number'), 'collateral_enabled_disabled_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_collateral_enabled_disabled_event_event_name'), 'collateral_enabled_disabled_event', ['event_name'], unique=False)
    op.create_table('deposit_event',
    sa.Column('user', sa.String(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('face_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_deposit_event_block_number'), 'deposit_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_deposit_event_event_name'), 'deposit_event', ['event_name'], unique=False)
    op.create_table('liquidation_event',
    sa.Column('liquidator', sa.String(), nullable=False),
    sa.Column('user', sa.String(), nullable=False),
    sa.Column('debt_token', sa.String(), nullable=False),
    sa.Column('debt_raw_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('debt_face_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('collateral_token', sa.String(), nullable=False),
    sa.Column('collateral_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_liquidation_event_block_number'), 'liquidation_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_liquidation_event_event_name'), 'liquidation_event', ['event_name'], unique=False)
    op.create_table('repayment_event',
    sa.Column('repayer', sa.String(), nullable=False),
    sa.Column('beneficiary', sa.String(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('raw_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('face_amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repayment_event_block_number'), 'repayment_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_repayment_event_event_name'), 'repayment_event', ['event_name'], unique=False)
    op.create_table('withdrawal_event',
    sa.Column('user', sa.String(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=38, scale=18), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('event_name', sa.String(), nullable=False),
    sa.Column('block_number', sa.Integer(), nullable=False),
    sa.Column('protocol_id', sqlalchemy_utils.types.choice.ChoiceType(ProtocolIDs), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_withdrawal_event_block_number'), 'withdrawal_event', ['block_number'], unique=False)
    op.create_index(op.f('ix_withdrawal_event_event_name'), 'withdrawal_event', ['event_name'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Revert the database schema changes for ZkLend events.
    
    Removes tables and relationships that were added for ZkLend event tracking,
    restoring the database to its previous state.
    """
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_withdrawal_event_event_name'), table_name='withdrawal_event')
    op.drop_index(op.f('ix_withdrawal_event_block_number'), table_name='withdrawal_event')
    op.drop_table('withdrawal_event')
    op.drop_index(op.f('ix_repayment_event_event_name'), table_name='repayment_event')
    op.drop_index(op.f('ix_repayment_event_block_number'), table_name='repayment_event')
    op.drop_table('repayment_event')
    op.drop_index(op.f('ix_liquidation_event_event_name'), table_name='liquidation_event')
    op.drop_index(op.f('ix_liquidation_event_block_number'), table_name='liquidation_event')
    op.drop_table('liquidation_event')
    op.drop_index(op.f('ix_deposit_event_event_name'), table_name='deposit_event')
    op.drop_index(op.f('ix_deposit_event_block_number'), table_name='deposit_event')
    op.drop_table('deposit_event')
    op.drop_index(op.f('ix_collateral_enabled_disabled_event_event_name'), table_name='collateral_enabled_disabled_event')
    op.drop_index(op.f('ix_collateral_enabled_disabled_event_block_number'), table_name='collateral_enabled_disabled_event')
    op.drop_table('collateral_enabled_disabled_event')
    op.drop_index(op.f('ix_borrowing_event_event_name'), table_name='borrowing_event')
    op.drop_index(op.f('ix_borrowing_event_block_number'), table_name='borrowing_event')
    op.drop_table('borrowing_event')
    op.drop_index(op.f('ix_accumulators_sync_event_event_name'), table_name='accumulators_sync_event')
    op.drop_index(op.f('ix_accumulators_sync_event_block_number'), table_name='accumulators_sync_event')
    op.drop_table('accumulators_sync_event')
    # ### end Alembic commands ###