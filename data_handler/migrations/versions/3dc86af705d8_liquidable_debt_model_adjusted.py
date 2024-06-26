"""liquidable debt model adjusted

Revision ID: 3dc86af705d8
Revises: 593bb0a7d06b
Create Date: 2024-06-11 19:40:57.930031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

from handlers.liquidable_debt.values import LendingProtocolNames

# revision identifiers, used by Alembic.
revision: str = '3dc86af705d8'
down_revision: Union[str, None] = '593bb0a7d06b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('liquidable_debt',
                  sa.Column('protocol_name', sqlalchemy_utils.types.choice.ChoiceType(
                      choices=LendingProtocolNames, impl=sa.String()
                  ), nullable=False)
    )
    op.add_column('liquidable_debt', sa.Column('collateral_token_price', sa.DECIMAL(), nullable=False))
    op.drop_column('liquidable_debt', 'protocol')
    op.drop_column('liquidable_debt', 'price')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('liquidable_debt', sa.Column('price', sa.NUMERIC(), autoincrement=False, nullable=False))
    op.add_column('liquidable_debt', sa.Column('protocol', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_column('liquidable_debt', 'collateral_token_price')
    op.drop_column('liquidable_debt', 'protocol_name')
    # ### end Alembic commands ###
