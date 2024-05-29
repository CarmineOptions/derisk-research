"""Merge branch A and B

Revision ID: 841f539c35e9
Revises: 2a2e310c0e6c, 26bebf9e427d
Create Date: 2024-05-29 19:27:28.718084

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = "841f539c35e9"
down_revision: Union[str, None] = ("2a2e310c0e6c", "26bebf9e427d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
