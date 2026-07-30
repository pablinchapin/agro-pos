"""seed grain_types data

Revision ID: f549345b2818
Revises: 39c7250b2c97
Create Date: 2026-07-09 20:34:08.710823

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f549345b2818'
down_revision: Union[str, None] = '39c7250b2c97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.bulk_insert(
        sa.table(
            "grain_types",
            sa.column("name", sa.String),
            sa.column("unit", sa.String),
        ),
        [
            {"name": "Café", "unit": "lb"},
            {"name": "Maíz", "unit": "lb"},
            {"name": "Frijol", "unit": "lb"},
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM grain_types WHERE name IN ('Café', 'Maíz', 'Frijol')")
