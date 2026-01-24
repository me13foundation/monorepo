"""Ensure PUBMED is present in sourcetypeenum."""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "c58bc6f7ca55"
down_revision: str | Sequence[str] | None = (
    "20260123_add_pub_extractions",
    "5f3b2d1c4e7a",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("ALTER TYPE sourcetypeenum ADD VALUE IF NOT EXISTS 'PUBMED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Enum value removal is not easily reversible in Postgres.
    return
