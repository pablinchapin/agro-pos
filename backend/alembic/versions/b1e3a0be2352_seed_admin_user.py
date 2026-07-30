"""seed admin user

Revision ID: b1e3a0be2352
Revises: fc31f50a9b0b
Create Date: 2026-07-27 15:18:45.525532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Hash the seed password directly with passlib in the migration itself —
# never call into app code (app.core.security) from a migration, since the
# app layer can change independently of historical migrations.
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = 'b1e3a0be2352'
down_revision: Union[str, None] = 'fc31f50a9b0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    hashed_password = pwd_context.hash("Admin1234!")

    op.bulk_insert(
        sa.table(
            "users",
            sa.column("username", sa.String),
            sa.column("hashed_password", sa.String),
            sa.column("role", sa.String),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {
                "username": "admin",
                "hashed_password": hashed_password,
                "role": "admin",
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE username = 'admin'")
