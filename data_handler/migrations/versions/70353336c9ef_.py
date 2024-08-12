"""empty message

Revision ID: 70353336c9ef
Revises: 4280b8a75614, efd02f93572b
Create Date: 2024-08-06 17:35:36.804256

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "70353336c9ef"
down_revision: Union[str, None] = ("4280b8a75614", "efd02f93572b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
