"""add space scoped discovery scaffolding

Revision ID: 45aad920411e
Revises: e9c9f4b2fe38
Create Date: 2025-11-14 21:54:39.353572

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45aad920411e"
down_revision: str | Sequence[str] | None = "e9c9f4b2fe38"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_ENUM_NAME = "data_source_permission_level"
DEFAULT_SPACE_ID = "560e9e0b-13bd-4337-a55d-2d3f650e451f"


def upgrade() -> None:
    """Upgrade schema to support space-scoped discovery."""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    inspector = sa.inspect(bind)

    # --- Data source permission levels ------------------------------------
    permission_enum = sa.Enum(
        "blocked",
        "visible",
        "available",
        name=PERMISSION_ENUM_NAME,
    )
    if dialect_name != "sqlite":
        permission_enum.create(bind, checkfirst=True)

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("data_source_activation_rules")
    }
    added_permission_column = False
    if "permission_level" not in existing_columns:
        op.add_column(
            "data_source_activation_rules",
            sa.Column(
                "permission_level",
                permission_enum if dialect_name != "sqlite" else sa.String(32),
                nullable=False,
                server_default="available",
            ),
        )
        added_permission_column = True

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("data_source_activation_rules")
    }
    if "ix_data_source_activation_rules_permission_level" not in existing_indexes:
        op.create_index(
            "ix_data_source_activation_rules_permission_level",
            "data_source_activation_rules",
            ["permission_level"],
        )
    if "ix_data_source_activation_rules_space_permission" not in existing_indexes:
        op.create_index(
            "ix_data_source_activation_rules_space_permission",
            "data_source_activation_rules",
            ["research_space_id", "permission_level"],
        )

    # Align existing data with permission levels
    available_value = "available"
    blocked_value = "blocked"
    update_sql = """
        UPDATE data_source_activation_rules
        SET permission_level = CASE
            WHEN COALESCE(is_active, FALSE) IS TRUE THEN {available}
            ELSE {blocked}
        END
    """
    if dialect_name == "postgresql":
        update_sql = update_sql.format(
            available=f"'{available_value}'::{PERMISSION_ENUM_NAME}",
            blocked=f"'{blocked_value}'::{PERMISSION_ENUM_NAME}",
        )
    else:
        update_sql = update_sql.format(
            available=f"'{available_value}'",
            blocked=f"'{blocked_value}'",
        )
    op.execute(sa.text(update_sql))

    # Remove server default now that data migrated
    if added_permission_column:
        with op.batch_alter_table("data_source_activation_rules") as batch:
            batch.alter_column(
                "permission_level",
                server_default=None,
                existing_type=(
                    permission_enum if dialect_name != "sqlite" else sa.String(32)
                ),
            )

    # --- Data discovery sessions must belong to a space --------------------
    op.execute(
        sa.text(
            """
            UPDATE data_discovery_sessions
            SET research_space_id = :default_space
            WHERE research_space_id IS NULL
            """,
        ).bindparams(default_space=DEFAULT_SPACE_ID),
    )

    with op.batch_alter_table("data_discovery_sessions") as batch:
        batch.alter_column(
            "research_space_id",
            existing_type=sa.String(36),
            nullable=False,
        )
        batch.create_index(
            "ix_data_discovery_sessions_space_owner",
            ["research_space_id", "owner_id"],
            unique=False,
        )


def downgrade() -> None:
    """Revert schema changes."""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    inspector = sa.inspect(bind)

    with op.batch_alter_table("data_discovery_sessions") as batch:
        batch.drop_index("ix_data_discovery_sessions_space_owner")
        batch.alter_column(
            "research_space_id",
            existing_type=sa.String(36),
            nullable=True,
        )

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("data_source_activation_rules")
    }
    if "ix_data_source_activation_rules_space_permission" in existing_indexes:
        op.drop_index(
            "ix_data_source_activation_rules_space_permission",
            table_name="data_source_activation_rules",
        )
    if "ix_data_source_activation_rules_permission_level" in existing_indexes:
        op.drop_index(
            "ix_data_source_activation_rules_permission_level",
            table_name="data_source_activation_rules",
        )
    existing_columns = {
        column["name"]
        for column in inspector.get_columns("data_source_activation_rules")
    }
    if "permission_level" in existing_columns:
        op.drop_column("data_source_activation_rules", "permission_level")

    if dialect_name != "sqlite":
        permission_enum = sa.Enum(
            "blocked",
            "visible",
            "available",
            name=PERMISSION_ENUM_NAME,
        )
        permission_enum.drop(bind, checkfirst=True)
