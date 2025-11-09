"""Add research_space_id to reviews table

Revision ID: 3677d42fb8a1
Revises: f251af2b636a
Create Date: 2025-11-07 16:52:36.819339

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3677d42fb8a1"
down_revision: str | Sequence[str] | None = "f251af2b636a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add research_space_id column to reviews table."""
    # Check if column already exists (in case migration partially ran)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("reviews")]

    if "research_space_id" not in columns:
        # SQLite doesn't support adding foreign keys after table creation
        # Use batch mode for SQLite compatibility
        with op.batch_alter_table("reviews", schema=None) as batch_op:
            # Add research_space_id column
            batch_op.add_column(
                sa.Column(
                    "research_space_id",
                    sa.String(length=36),  # UUID as string for SQLite compatibility
                    nullable=True,
                ),
            )

            # Create index for research_space_id
            batch_op.create_index(
                "ix_reviews_research_space_id",
                ["research_space_id"],
            )

            # Add foreign key constraint (batch mode supports this in SQLite)
            batch_op.create_foreign_key(
                "fk_reviews_research_space_id",
                "research_spaces",
                ["research_space_id"],
                ["id"],
            )
    else:
        # Column exists, just ensure index exists
        indexes = [idx["name"] for idx in inspector.get_indexes("reviews")]
        if "ix_reviews_research_space_id" not in indexes:
            op.create_index(
                "ix_reviews_research_space_id",
                "reviews",
                ["research_space_id"],
            )


def downgrade() -> None:
    """Remove research_space_id column from reviews table."""
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        # Drop foreign key constraint
        batch_op.drop_constraint("fk_reviews_research_space_id", type_="foreignkey")

        # Drop index
        batch_op.drop_index("ix_reviews_research_space_id")

        # Drop column
        batch_op.drop_column("research_space_id")
