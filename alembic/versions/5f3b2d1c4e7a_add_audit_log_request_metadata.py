"""Add request metadata fields to audit logs.

Revision ID: 5f3b2d1c4e7a
Revises: e9c9f4b2fe38
Create Date: 2025-11-05 00:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "5f3b2d1c4e7a"
down_revision: str | Sequence[str] | None = "e9c9f4b2fe38"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add request metadata fields to audit logs."""
    op.add_column(
        "audit_logs",
        sa.Column("request_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("ip_address", sa.String(length=45), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("user_agent", sa.Text(), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("success", sa.Boolean(), nullable=True),
    )
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])


def downgrade() -> None:
    """Remove request metadata fields from audit logs."""
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_column("audit_logs", "success")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "ip_address")
    op.drop_column("audit_logs", "request_id")
