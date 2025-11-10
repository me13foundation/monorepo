"""Add created_at and updated_at columns to query_test_results table in Postgres

Revision ID: 2855ecc68ef0
Revises: c41dc298ca65
Create Date: 2025-11-09 19:48:59.948957

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2855ecc68ef0"
down_revision: str | Sequence[str] | None = "c41dc298ca65"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add created_at and updated_at columns to query_test_results table
    op.add_column(
        "query_test_results",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "query_test_results",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop created_at and updated_at columns from query_test_results table
    op.drop_column("query_test_results", "updated_at")
    op.drop_column("query_test_results", "created_at")
