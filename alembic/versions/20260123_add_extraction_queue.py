"""add extraction queue table

Revision ID: 20260123_add_extraction_queue
Revises: 599303884b08
Create Date: 2026-01-23
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "20260123_add_extraction_queue"
down_revision: str | Sequence[str] | None = "599303884b08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("extraction_queue"):
        return

    status_enum = sa.Enum(
        "pending",
        "processing",
        "completed",
        "failed",
        name="extraction_status_enum",
    )

    op.create_table(
        "extraction_queue",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("publication_id", sa.Integer(), nullable=False),
        sa.Column("pubmed_id", sa.String(length=20), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("ingestion_job_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "extraction_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "metadata_payload",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "queued_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
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
            name=op.f("fk_extraction_queue_publication_id_publications"),
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["user_data_sources.id"],
            name=op.f("fk_extraction_queue_source_id_user_data_sources"),
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_job_id"],
            ["ingestion_jobs.id"],
            name=op.f("fk_extraction_queue_ingestion_job_id_ingestion_jobs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extraction_queue")),
        sa.UniqueConstraint(
            "publication_id",
            "source_id",
            "extraction_version",
            name="uq_extraction_queue_pub_source_version",
        ),
    )

    op.create_index(
        op.f("ix_extraction_queue_status"),
        "extraction_queue",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extraction_queue_publication_id"),
        "extraction_queue",
        ["publication_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extraction_queue_source_id"),
        "extraction_queue",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extraction_queue_ingestion_job_id"),
        "extraction_queue",
        ["ingestion_job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extraction_queue_extraction_version"),
        "extraction_queue",
        ["extraction_version"],
        unique=False,
    )
    op.create_index(
        op.f("ix_extraction_queue_pubmed_id"),
        "extraction_queue",
        ["pubmed_id"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("extraction_queue"):
        return

    op.drop_index(op.f("ix_extraction_queue_pubmed_id"), table_name="extraction_queue")
    op.drop_index(
        op.f("ix_extraction_queue_extraction_version"),
        table_name="extraction_queue",
    )
    op.drop_index(
        op.f("ix_extraction_queue_ingestion_job_id"),
        table_name="extraction_queue",
    )
    op.drop_index(
        op.f("ix_extraction_queue_source_id"),
        table_name="extraction_queue",
    )
    op.drop_index(
        op.f("ix_extraction_queue_publication_id"),
        table_name="extraction_queue",
    )
    op.drop_index(op.f("ix_extraction_queue_status"), table_name="extraction_queue")
    op.drop_table("extraction_queue")

    status_enum = sa.Enum(
        "pending",
        "processing",
        "completed",
        "failed",
        name="extraction_status_enum",
    )
    status_enum.drop(op.get_bind(), checkfirst=True)
