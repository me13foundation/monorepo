"""Add table for data source activation policies."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d6a0f2b5c1e"
down_revision: str | None = "2855ecc68ef0"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("data_source_activation_rules"):
        return
    op.create_table(
        "data_source_activation_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("catalog_entry_id", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("research_space_id", sa.UUID(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("updated_by", sa.UUID(), nullable=False),
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
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["catalog_entry_id"],
            ["source_catalog_entries.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["research_space_id"],
            ["research_spaces.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "catalog_entry_id",
            "scope",
            "research_space_id",
            name="uq_data_source_activation_scope",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_data_source_activation_rules_catalog_entry_id",
        "data_source_activation_rules",
        ["catalog_entry_id"],
    )
    op.create_index(
        "ix_data_source_activation_rules_scope",
        "data_source_activation_rules",
        ["scope"],
    )
    op.create_index(
        "ix_data_source_activation_rules_research_space_id",
        "data_source_activation_rules",
        ["research_space_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("data_source_activation_rules"):
        return
    op.drop_index(
        "ix_data_source_activation_rules_research_space_id",
        table_name="data_source_activation_rules",
    )
    op.drop_index(
        "ix_data_source_activation_rules_scope",
        table_name="data_source_activation_rules",
    )
    op.drop_index(
        "ix_data_source_activation_rules_catalog_entry_id",
        table_name="data_source_activation_rules",
    )
    op.drop_table("data_source_activation_rules")
