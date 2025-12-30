"""add_uppercase_pubmed_to_sourcetypeenum

Revision ID: 599303884b08
Revises: 20250211_discovery_jobs
Create Date: 2025-11-23 13:51:11.728247

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "599303884b08"
down_revision: str | Sequence[str] | None = "20250211_discovery_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the PUBMED value to sourcetypeenum."""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    # Add 'PUBMED' to match the SQLAlchemy Enum member name,
    # which is what SQLAlchemy persists by default.
    # (Previous migration added 'pubmed', but SQLAlchemy sends 'PUBMED')
    op.execute("ALTER TYPE sourcetypeenum ADD VALUE IF NOT EXISTS 'PUBMED'")


def downgrade() -> None:
    """Downgrade schema."""
    # Cannot easily remove enum value in PostgreSQL
