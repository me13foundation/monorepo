"""add_data_sources_tables

Revision ID: 841d4a55d87e
Revises: add_curation_tables_20251102
Create Date: 2025-11-02 23:04:35.809964

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "841d4a55d87e"
down_revision: str | Sequence[str] | None = "add_curation_tables_20251102"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types
    source_type_enum = sa.Enum(
        "FILE_UPLOAD",
        "API",
        "DATABASE",
        "WEB_SCRAPING",
        name="sourcetypeenum",
    )

    source_status_enum = sa.Enum(
        "DRAFT",
        "ACTIVE",
        "INACTIVE",
        "ERROR",
        "PENDING_REVIEW",
        "ARCHIVED",
        name="sourcestatusenum",
    )

    template_category_enum = sa.Enum(
        "CLINICAL",
        "RESEARCH",
        "LITERATURE",
        "GENOMIC",
        "PHENOTYPIC",
        "ONTOLOGY",
        "OTHER",
        name="templatecategoryenum",
    )

    ingestion_status_enum = sa.Enum(
        "PENDING",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "PARTIAL",
        name="ingestionstatusenum",
    )

    ingestion_trigger_enum = sa.Enum(
        "MANUAL",
        "SCHEDULED",
        "API",
        "WEBHOOK",
        "RETRY",
        name="ingestiontriggerenum",
    )

    # Create source_templates table
    op.create_table(
        "source_templates",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", template_category_enum, nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("schema_definition", sa.JSON(), nullable=False),
        sa.Column("validation_rules", sa.JSON(), nullable=False),
        sa.Column("ui_config", sa.JSON(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("approved_at", sa.String(30), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("compatibility_version", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for source_templates
    op.create_index(
        "ix_source_templates_created_by",
        "source_templates",
        ["created_by"],
    )
    op.create_index("ix_source_templates_category", "source_templates", ["category"])
    op.create_index(
        "ix_source_templates_source_type",
        "source_templates",
        ["source_type"],
    )
    op.create_index("ix_source_templates_is_public", "source_templates", ["is_public"])
    op.create_index(
        "ix_source_templates_is_approved",
        "source_templates",
        ["is_approved"],
    )

    # Create user_data_sources table
    op.create_table(
        "user_data_sources",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("template_id", sa.String(36), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("status", source_status_enum, nullable=False),
        sa.Column("ingestion_schedule", sa.JSON(), nullable=False),
        sa.Column("quality_metrics", sa.JSON(), nullable=False),
        sa.Column("last_ingested_at", sa.String(30), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["source_templates.id"],
            ondelete="SET NULL",
        ),
    )

    # Create indexes for user_data_sources
    op.create_index("ix_user_data_sources_owner_id", "user_data_sources", ["owner_id"])
    op.create_index(
        "ix_user_data_sources_source_type",
        "user_data_sources",
        ["source_type"],
    )
    op.create_index("ix_user_data_sources_status", "user_data_sources", ["status"])
    op.create_index(
        "ix_user_data_sources_template_id",
        "user_data_sources",
        ["template_id"],
    )

    # Create ingestion_jobs table
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("trigger", ingestion_trigger_enum, nullable=False),
        sa.Column("triggered_by", sa.String(36), nullable=True),
        sa.Column("triggered_at", sa.String(30), nullable=False),
        sa.Column("status", ingestion_status_enum, nullable=False),
        sa.Column("started_at", sa.String(30), nullable=True),
        sa.Column("completed_at", sa.String(30), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("source_config_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["user_data_sources.id"],
            ondelete="CASCADE",
        ),
    )

    # Create indexes for ingestion_jobs
    op.create_index("ix_ingestion_jobs_source_id", "ingestion_jobs", ["source_id"])
    op.create_index(
        "ix_ingestion_jobs_triggered_by",
        "ingestion_jobs",
        ["triggered_by"],
    )
    op.create_index(
        "ix_ingestion_jobs_triggered_at",
        "ingestion_jobs",
        ["triggered_at"],
    )
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table("ingestion_jobs")
    op.drop_table("user_data_sources")
    op.drop_table("source_templates")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS sourcetypeenum")
    op.execute("DROP TYPE IF EXISTS sourcestatusenum")
    op.execute("DROP TYPE IF EXISTS templatecategoryenum")
    op.execute("DROP TYPE IF EXISTS ingestionstatusenum")
    op.execute("DROP TYPE IF EXISTS ingestiontriggerenum")
