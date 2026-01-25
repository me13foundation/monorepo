"""add_mechanisms_table

Revision ID: d2a4f7e3c1b9
Revises: c58bc6f7ca55
Create Date: 2026-01-25 00:00:00.000000

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "d2a4f7e3c1b9"
down_revision: str | Sequence[str] | None = "c58bc6f7ca55"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "mechanisms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_tier", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("protein_domains", sa.JSON(), nullable=False),
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
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_mechanisms_name", "mechanisms", ["name"])

    op.create_table(
        "mechanism_phenotypes",
        sa.Column(
            "mechanism_id",
            sa.Integer(),
            sa.ForeignKey("mechanisms.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "phenotype_id",
            sa.Integer(),
            sa.ForeignKey("phenotypes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_mechanism_phenotypes_mechanism_id",
        "mechanism_phenotypes",
        ["mechanism_id"],
    )
    op.create_index(
        "ix_mechanism_phenotypes_phenotype_id",
        "mechanism_phenotypes",
        ["phenotype_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_mechanism_phenotypes_phenotype_id",
        table_name="mechanism_phenotypes",
    )
    op.drop_index(
        "ix_mechanism_phenotypes_mechanism_id",
        table_name="mechanism_phenotypes",
    )
    op.drop_table("mechanism_phenotypes")
    op.drop_index("ix_mechanisms_name", table_name="mechanisms")
    op.drop_table("mechanisms")
