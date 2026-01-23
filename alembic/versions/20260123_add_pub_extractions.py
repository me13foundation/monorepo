"""add publication extractions table

Revision ID: 20260123_add_pub_extractions
Revises: 20260123_fix_ing_job_md
Create Date: 2026-01-23
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "20260123_add_pub_extractions"
down_revision: str | Sequence[str] | None = "20260123_fix_ing_job_md"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("publication_extractions"):
        return

    outcome_enum = sa.Enum(
        "completed",
        "failed",
        "skipped",
        name="extraction_outcome_enum",
    )

    op.create_table(
        "publication_extractions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("publication_id", sa.Integer(), nullable=False),
        sa.Column("pubmed_id", sa.String(length=20), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("ingestion_job_id", sa.UUID(), nullable=False),
        sa.Column("queue_item_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            outcome_enum,
            nullable=False,
            server_default="completed",
        ),
        sa.Column(
            "extraction_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column("processor_name", sa.String(length=120), nullable=False),
        sa.Column("processor_version", sa.String(length=50), nullable=True),
        sa.Column("text_source", sa.String(length=30), nullable=False),
        sa.Column("document_reference", sa.String(length=500), nullable=True),
        sa.Column(
            "facts",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata_payload",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "extracted_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["publications.id"],
            name=op.f("fk_publication_extractions_publication_id_publications"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["user_data_sources.id"],
            name=op.f("fk_publication_extractions_source_id_user_data_sources"),
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_job_id"],
            ["ingestion_jobs.id"],
            name=op.f("fk_publication_extractions_ingestion_job_id_ingestion_jobs"),
        ),
        sa.ForeignKeyConstraint(
            ["queue_item_id"],
            ["extraction_queue.id"],
            name=op.f("fk_publication_extractions_queue_item_id_extraction_queue"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_publication_extractions")),
        sa.UniqueConstraint(
            "queue_item_id",
            name="uq_publication_extractions_queue_item",
        ),
    )

    op.create_index(
        op.f("ix_publication_extractions_publication_id"),
        "publication_extractions",
        ["publication_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_publication_extractions_pubmed_id"),
        "publication_extractions",
        ["pubmed_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_publication_extractions_source_id"),
        "publication_extractions",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_publication_extractions_ingestion_job_id"),
        "publication_extractions",
        ["ingestion_job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_publication_extractions_queue_item_id"),
        "publication_extractions",
        ["queue_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_publication_extractions_status"),
        "publication_extractions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_publication_extractions_extraction_version"),
        "publication_extractions",
        ["extraction_version"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("publication_extractions"):
        return

    op.drop_index(
        op.f("ix_publication_extractions_extraction_version"),
        table_name="publication_extractions",
    )
    op.drop_index(
        op.f("ix_publication_extractions_status"),
        table_name="publication_extractions",
    )
    op.drop_index(
        op.f("ix_publication_extractions_queue_item_id"),
        table_name="publication_extractions",
    )
    op.drop_index(
        op.f("ix_publication_extractions_ingestion_job_id"),
        table_name="publication_extractions",
    )
    op.drop_index(
        op.f("ix_publication_extractions_source_id"),
        table_name="publication_extractions",
    )
    op.drop_index(
        op.f("ix_publication_extractions_pubmed_id"),
        table_name="publication_extractions",
    )
    op.drop_index(
        op.f("ix_publication_extractions_publication_id"),
        table_name="publication_extractions",
    )
    op.drop_table("publication_extractions")

    outcome_enum = sa.Enum(
        "completed",
        "failed",
        "skipped",
        name="extraction_outcome_enum",
    )
    outcome_enum.drop(op.get_bind(), checkfirst=True)
