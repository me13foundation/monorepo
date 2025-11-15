"""Merge pubmed source type branch."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e9c9f4b2fe38"
down_revision: str | Sequence[str] | None = ("0d6a0f2b5c1e", "7c2b1df29f25")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op merge upgrade."""


def downgrade() -> None:
    """No-op merge downgrade."""
