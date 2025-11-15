"""Add PubMed source type to source type enum."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c2b1df29f25"
down_revision: str | Sequence[str] | None = "841d4a55d87e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the pubmed value to sourcetypeenum."""
    op.execute("ALTER TYPE sourcetypeenum ADD VALUE IF NOT EXISTS 'pubmed'")


def downgrade() -> None:
    """Remove the pubmed value from sourcetypeenum."""
    bind = op.get_bind()

    # Remove any rows using the pubmed value to avoid cast failures.
    bind.execute(
        sa.text("DELETE FROM user_data_sources WHERE source_type = 'pubmed'"),
    )
    bind.execute(
        sa.text("DELETE FROM source_templates WHERE source_type = 'pubmed'"),
    )

    # Recreate the enum without the pubmed value.
    op.execute("ALTER TYPE sourcetypeenum RENAME TO sourcetypeenum_old")
    new_enum = sa.Enum(
        "file_upload",
        "api",
        "database",
        "web_scraping",
        name="sourcetypeenum",
    )
    new_enum.create(bind, checkfirst=False)

    op.execute(
        "ALTER TABLE user_data_sources "
        "ALTER COLUMN source_type TYPE sourcetypeenum "
        "USING source_type::text::sourcetypeenum",
    )
    op.execute(
        "ALTER TABLE source_templates "
        "ALTER COLUMN source_type TYPE sourcetypeenum "
        "USING source_type::text::sourcetypeenum",
    )

    op.execute("DROP TYPE sourcetypeenum_old")
