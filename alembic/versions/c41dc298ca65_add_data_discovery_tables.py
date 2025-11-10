"""add_data_discovery_tables

Revision ID: c41dc298ca65
Revises: 3677d42fb8a1
Create Date: 2025-11-09 12:56:45.665892

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c41dc298ca65"
down_revision: str | Sequence[str] | None = "3677d42fb8a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables already exist (they may have been created manually)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    def table_exists(name: str) -> bool:
        return inspector.has_table(name)

    dialect_name = conn.dialect.name
    uuid_type: sa.types.TypeEngine = sa.String(36)
    if dialect_name == "postgresql":
        uuid_type = postgresql.UUID(as_uuid=False)

    # Create source_catalog_entries table
    if not table_exists("source_catalog_entries"):
        op.create_table(
            "source_catalog_entries",
            sa.Column("id", sa.String(100), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("category", sa.String(100), nullable=False),
            sa.Column("subcategory", sa.String(100), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=False),
            sa.Column("param_type", sa.String(50), nullable=False),
            sa.Column("url_template", sa.Text(), nullable=True),
            sa.Column("data_format", sa.String(50), nullable=True),
            sa.Column("api_endpoint", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "requires_auth",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("success_rate", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("source_template_id", uuid_type, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["source_template_id"],
                ["source_templates.id"],
            ),
        )

        # Create indexes for source_catalog_entries
        op.create_index(
            "ix_source_catalog_entries_category",
            "source_catalog_entries",
            ["category"],
        )
        op.create_index(
            "ix_source_catalog_entries_param_type",
            "source_catalog_entries",
            ["param_type"],
        )
        op.create_index(
            "ix_source_catalog_entries_source_template_id",
            "source_catalog_entries",
            ["source_template_id"],
        )

    # Create data_discovery_sessions table
    if not table_exists("data_discovery_sessions"):
        op.create_table(
            "data_discovery_sessions",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("owner_id", uuid_type, nullable=False),
            sa.Column("research_space_id", uuid_type, nullable=True),
            sa.Column(
                "name",
                sa.String(200),
                nullable=False,
                server_default="Untitled Session",
            ),
            sa.Column("gene_symbol", sa.String(100), nullable=True),
            sa.Column("search_term", sa.Text(), nullable=True),
            sa.Column(
                "selected_sources",
                sa.JSON(),
                nullable=False,
                server_default="[]",
            ),
            sa.Column("tested_sources", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column(
                "total_tests_run",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "successful_tests",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "last_activity_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["research_space_id"],
                ["research_spaces.id"],
            ),
        )

        # Create indexes for data_discovery_sessions
        op.create_index(
            "ix_data_discovery_sessions_owner_id",
            "data_discovery_sessions",
            ["owner_id"],
        )
        op.create_index(
            "ix_data_discovery_sessions_research_space_id",
            "data_discovery_sessions",
            ["research_space_id"],
        )

    # Create query_test_results table
    if not table_exists("query_test_results"):
        op.create_table(
            "query_test_results",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("session_id", uuid_type, nullable=False),
            sa.Column("catalog_entry_id", sa.String(100), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("gene_symbol", sa.String(100), nullable=True),
            sa.Column("search_term", sa.Text(), nullable=True),
            sa.Column("response_data", sa.JSON(), nullable=True),
            sa.Column("response_url", sa.Text(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("execution_time_ms", sa.Integer(), nullable=True),
            sa.Column("data_quality_score", sa.Float(), nullable=True),
            sa.Column(
                "started_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["session_id"],
                ["data_discovery_sessions.id"],
            ),
            sa.ForeignKeyConstraint(
                ["catalog_entry_id"],
                ["source_catalog_entries.id"],
            ),
        )

        # Create indexes for query_test_results
        op.create_index(
            "ix_query_test_results_session_id",
            "query_test_results",
            ["session_id"],
        )
        op.create_index(
            "ix_query_test_results_catalog_entry_id",
            "query_test_results",
            ["catalog_entry_id"],
        )
        op.create_index(
            "ix_query_test_results_status",
            "query_test_results",
            ["status"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("ix_query_test_results_status", table_name="query_test_results")
    op.drop_index(
        "ix_query_test_results_catalog_entry_id",
        table_name="query_test_results",
    )
    op.drop_index("ix_query_test_results_session_id", table_name="query_test_results")
    op.drop_index(
        "ix_data_discovery_sessions_research_space_id",
        table_name="data_discovery_sessions",
    )
    op.drop_index(
        "ix_data_discovery_sessions_owner_id",
        table_name="data_discovery_sessions",
    )
    op.drop_index(
        "ix_source_catalog_entries_source_template_id",
        table_name="source_catalog_entries",
    )
    op.drop_index(
        "ix_source_catalog_entries_param_type",
        table_name="source_catalog_entries",
    )
    op.drop_index(
        "ix_source_catalog_entries_category",
        table_name="source_catalog_entries",
    )

    # Drop tables
    op.drop_table("query_test_results")
    op.drop_table("data_discovery_sessions")
    op.drop_table("source_catalog_entries")
