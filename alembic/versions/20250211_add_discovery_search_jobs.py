"""Add discovery search jobs and catalog capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "20250211_discovery_jobs"
down_revision: str | Sequence[str] | None = "5b3fb28e5ab2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect_name = bind.dialect.name
    uuid_type: sa.types.TypeEngine = sa.String(length=36)
    if dialect_name == "postgresql":
        uuid_type = postgresql.UUID(as_uuid=False)

    catalog_columns = {
        col["name"] for col in inspector.get_columns("source_catalog_entries")
    }
    if "query_capabilities" not in catalog_columns:
        op.add_column(
            "source_catalog_entries",
            sa.Column(
                "query_capabilities",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )
        op.execute(
            sa.text(
                "UPDATE source_catalog_entries SET query_capabilities = '{}' "
                "WHERE query_capabilities IS NULL",
            ),
        )
        with op.batch_alter_table("source_catalog_entries") as batch:
            batch.alter_column("query_capabilities", server_default=None)

    result_columns = {
        col["name"] for col in inspector.get_columns("query_test_results")
    }
    if "parameters_payload" not in result_columns:
        op.add_column(
            "query_test_results",
            sa.Column(
                "parameters_payload",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )
        op.execute(
            sa.text(
                "UPDATE query_test_results SET parameters_payload = '{}' "
                "WHERE parameters_payload IS NULL",
            ),
        )
        with op.batch_alter_table("query_test_results") as batch:
            batch.alter_column("parameters_payload", server_default=None)

    if not inspector.has_table("discovery_search_jobs"):
        op.create_table(
            "discovery_search_jobs",
            sa.Column("id", uuid_type, primary_key=True),
            sa.Column("owner_id", uuid_type, nullable=False),
            sa.Column("session_id", uuid_type, nullable=True),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("query_preview", sa.Text(), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column(
                "total_results",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "result_payload",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("storage_key", sa.String(length=512), nullable=True),
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
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ("session_id",),
                ("data_discovery_sessions.id",),
                name="fk_discovery_search_jobs_session",
            ),
        )
        op.create_index(
            "ix_discovery_search_jobs_owner",
            "discovery_search_jobs",
            ["owner_id"],
        )
        op.create_index(
            "ix_discovery_search_jobs_session",
            "discovery_search_jobs",
            ["session_id"],
        )
        op.create_index(
            "ix_discovery_search_jobs_provider",
            "discovery_search_jobs",
            ["provider"],
        )
        op.create_index(
            "ix_discovery_search_jobs_status",
            "discovery_search_jobs",
            ["status"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("discovery_search_jobs"):
        op.drop_index(
            "ix_discovery_search_jobs_status",
            table_name="discovery_search_jobs",
        )
        op.drop_index(
            "ix_discovery_search_jobs_provider",
            table_name="discovery_search_jobs",
        )
        op.drop_index(
            "ix_discovery_search_jobs_session",
            table_name="discovery_search_jobs",
        )
        op.drop_index(
            "ix_discovery_search_jobs_owner",
            table_name="discovery_search_jobs",
        )
        op.drop_table("discovery_search_jobs")

    result_columns = {
        col["name"] for col in inspector.get_columns("query_test_results")
    }
    if "parameters_payload" in result_columns:
        op.drop_column("query_test_results", "parameters_payload")

    catalog_columns = {
        col["name"] for col in inspector.get_columns("source_catalog_entries")
    }
    if "query_capabilities" in catalog_columns:
        op.drop_column("source_catalog_entries", "query_capabilities")
