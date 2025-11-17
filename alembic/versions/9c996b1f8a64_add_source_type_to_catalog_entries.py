"""Add source_type to source catalog entries.

Revision ID: 9c996b1f8a64
Revises: 45aad920411e
Create Date: 2025-11-20 12:15:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c996b1f8a64"
down_revision: str | Sequence[str] | None = "45aad920411e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_SOURCE_TYPE = "api"
SOURCE_TYPE_OVERRIDES: dict[str, str] = {
    "pubmed": "pubmed",
    "omop": "database",
    "trinetx": "database",
    "ukbiobank": "database",
    "finngen": "database",
    "marketscan": "database",
    "dbgap": "database",
    "stjude_cloud": "database",
    "reddit": "web_scraping",
    "patientslikeme": "web_scraping",
}


def upgrade() -> None:
    """Add source_type column and populate existing rows."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {
        column["name"] for column in inspector.get_columns("source_catalog_entries")
    }
    if "source_type" not in existing_columns:
        op.add_column(
            "source_catalog_entries",
            sa.Column(
                "source_type",
                sa.String(length=50),
                nullable=False,
                server_default=DEFAULT_SOURCE_TYPE,
            ),
        )

    # Populate override values for known entries
    for entry_id, source_type in SOURCE_TYPE_OVERRIDES.items():
        op.execute(
            sa.text(
                """
                UPDATE source_catalog_entries
                SET source_type = :source_type
                WHERE id = :entry_id
                """,
            ).bindparams(source_type=source_type, entry_id=entry_id),
        )

    # Ensure all rows have a value (covers legacy rows and new inserts)
    op.execute(
        sa.text(
            """
            UPDATE source_catalog_entries
            SET source_type = :default_type
            WHERE source_type IS NULL OR source_type = ''
            """,
        ).bindparams(default_type=DEFAULT_SOURCE_TYPE),
    )


def downgrade() -> None:
    """Remove source_type column."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {
        column["name"] for column in inspector.get_columns("source_catalog_entries")
    }
    if "source_type" in existing_columns:
        op.drop_column("source_catalog_entries", "source_type")
