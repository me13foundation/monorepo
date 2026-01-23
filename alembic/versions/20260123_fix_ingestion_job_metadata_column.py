"""fix ingestion_jobs job_metadata column

Revision ID: 20260123_fix_ing_job_md
Revises: 20260123_add_extraction_queue
Create Date: 2026-01-23
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "20260123_fix_ing_job_md"
down_revision: str | Sequence[str] | None = "20260123_add_extraction_queue"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ingestion_jobs"):
        return

    columns = _column_names(inspector, "ingestion_jobs")
    has_metadata = "metadata" in columns
    has_job_metadata = "job_metadata" in columns

    if has_job_metadata:
        return

    if has_metadata and bind.dialect.name == "postgresql":
        op.alter_column(
            "ingestion_jobs",
            "metadata",
            new_column_name="job_metadata",
            existing_type=sa.JSON(),
        )
        return

    op.add_column(
        "ingestion_jobs",
        sa.Column(
            "job_metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    if has_metadata:
        op.execute("UPDATE ingestion_jobs SET job_metadata = metadata")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ingestion_jobs"):
        return

    columns = _column_names(inspector, "ingestion_jobs")
    has_metadata = "metadata" in columns
    has_job_metadata = "job_metadata" in columns

    if bind.dialect.name == "postgresql" and has_job_metadata and not has_metadata:
        op.alter_column(
            "ingestion_jobs",
            "job_metadata",
            new_column_name="metadata",
            existing_type=sa.JSON(),
        )
        return

    if has_job_metadata:
        op.drop_column("ingestion_jobs", "job_metadata")
