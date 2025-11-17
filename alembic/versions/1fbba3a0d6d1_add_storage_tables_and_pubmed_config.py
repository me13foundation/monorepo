"""Add storage tables and PubMed search config column."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "1fbba3a0d6d1"
down_revision: str | Sequence[str] | None = (
    "7c2b1df29f25",
    "0d6a0f2b5c1e",
    "9c996b1f8a64",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enum_exists(bind, name: str) -> bool:
    if bind.dialect.name != "postgresql":
        return False
    query = sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum_name)",
    )
    result = bind.execute(query, {"enum_name": name})
    return bool(result.scalar())


def _create_enum(
    bind,
    name: str,
    values: list[str],
) -> sa.Enum:
    enum = postgresql.ENUM(
        *values,
        name=name,
        create_type=False,
    )
    if not _enum_exists(bind, name):
        creator = postgresql.ENUM(*values, name=name)
        creator.create(bind, checkfirst=False)
    return enum


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    provider_enum = _create_enum(
        bind,
        "storageproviderenum",
        ["local_filesystem", "google_cloud_storage"],
    )
    operation_type_enum = _create_enum(
        bind,
        "storageoperationtypeenum",
        ["store", "retrieve", "delete", "list", "test"],
    )
    operation_status_enum = _create_enum(
        bind,
        "storageoperationstatusenum",
        ["success", "failed", "pending"],
    )
    health_status_enum = _create_enum(
        bind,
        "storagehealthstatusenum",
        ["healthy", "degraded", "offline"],
    )

    if not inspector.has_table("storage_configurations"):
        op.create_table(
            "storage_configurations",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False, unique=True),
            sa.Column("provider", provider_enum, nullable=False),
            sa.Column("config_data", sa.JSON(), nullable=False),
            sa.Column(
                "enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
            sa.Column(
                "supported_capabilities",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            ),
            sa.Column(
                "default_use_cases",
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
        )
        op.create_index(
            "ix_storage_configurations_provider",
            "storage_configurations",
            ["provider"],
        )
        op.create_index(
            "ix_storage_configurations_enabled",
            "storage_configurations",
            ["enabled"],
        )

    if not inspector.has_table("storage_operations"):
        op.create_table(
            "storage_operations",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "configuration_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "storage_configurations.id",
                    ondelete="CASCADE",
                ),
                nullable=False,
            ),
            sa.Column("user_id", sa.String(length=36), nullable=True),
            sa.Column("operation_type", operation_type_enum, nullable=False),
            sa.Column("key", sa.String(length=512), nullable=False),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
            sa.Column("status", operation_status_enum, nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "metadata_payload",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
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
        )
        op.create_index(
            "ix_storage_operations_configuration_id",
            "storage_operations",
            ["configuration_id"],
        )
        op.create_index(
            "ix_storage_operations_operation_type",
            "storage_operations",
            ["operation_type"],
        )
        op.create_index(
            "ix_storage_operations_status",
            "storage_operations",
            ["status"],
        )

    if not inspector.has_table("storage_health_snapshots"):
        op.create_table(
            "storage_health_snapshots",
            sa.Column(
                "configuration_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "storage_configurations.id",
                    ondelete="CASCADE",
                ),
                primary_key=True,
            ),
            sa.Column("provider", provider_enum, nullable=False),
            sa.Column("status", health_status_enum, nullable=False),
            sa.Column(
                "last_checked_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "details",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
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
        )

    discovery_columns = {
        column["name"] for column in inspector.get_columns("data_discovery_sessions")
    }
    if "pubmed_search_config" not in discovery_columns:
        op.add_column(
            "data_discovery_sessions",
            sa.Column(
                "pubmed_search_config",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
        )
        op.execute(
            sa.text(
                "UPDATE data_discovery_sessions "
                "SET pubmed_search_config = '{}' "
                "WHERE pubmed_search_config IS NULL",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    discovery_columns = {
        column["name"] for column in inspector.get_columns("data_discovery_sessions")
    }
    if "pubmed_search_config" in discovery_columns:
        op.drop_column("data_discovery_sessions", "pubmed_search_config")

    if inspector.has_table("storage_health_snapshots"):
        op.drop_table("storage_health_snapshots")

    if inspector.has_table("storage_operations"):
        op.drop_index(
            "ix_storage_operations_status",
            table_name="storage_operations",
        )
        op.drop_index(
            "ix_storage_operations_operation_type",
            table_name="storage_operations",
        )
        op.drop_index(
            "ix_storage_operations_configuration_id",
            table_name="storage_operations",
        )
        op.drop_table("storage_operations")

    if inspector.has_table("storage_configurations"):
        op.drop_index(
            "ix_storage_configurations_enabled",
            table_name="storage_configurations",
        )
        op.drop_index(
            "ix_storage_configurations_provider",
            table_name="storage_configurations",
        )
        op.drop_table("storage_configurations")

    for enum_name in [
        "storagehealthstatusenum",
        "storageoperationstatusenum",
        "storageoperationtypeenum",
        "storageproviderenum",
    ]:
        enum = postgresql.ENUM(name=enum_name)
        enum.drop(bind, checkfirst=True)
