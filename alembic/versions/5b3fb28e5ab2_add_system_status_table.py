"""Add system status table for maintenance mode."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "5b3fb28e5ab2"
down_revision: str | Sequence[str] | None = "1fbba3a0d6d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_status",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    default_state = {
        "is_active": False,
        "message": None,
        "activated_at": None,
        "activated_by": None,
        "last_updated_by": None,
        "last_updated_at": None,
    }
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO system_status (key, value)
            VALUES (:key, :value)
            ON CONFLICT (key) DO NOTHING
            """,
        ),
        {
            "key": "maintenance_mode",
            "value": json.dumps(default_state),
        },
    )


def downgrade() -> None:
    op.drop_table("system_status")
