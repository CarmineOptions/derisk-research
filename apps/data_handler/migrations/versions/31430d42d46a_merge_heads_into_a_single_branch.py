"""Merge heads into a single branch

Revision ID: 31430d42d46a
Revises: 509baf9251f2, e813bfbd573f
Create Date: 2024-07-31 09:11:22.426949

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31430d42d46a"
down_revision: Union[str, None] = ("509baf9251f2", "e813bfbd573f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Function to apply the upgrade migrations."""
    pass


def downgrade() -> None:
    """
    Reverts the database schema changes applied in the upgrade.
    """
    pass
