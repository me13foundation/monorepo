"""
Gene SQLAlchemy model for MED13 Resource Library.
Database representation of gene entities with relationships.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .variant import VariantModel


class GeneType(SQLEnum):
    """Gene type classification - matches Pydantic enum."""

    PROTEIN_CODING = "protein_coding"
    PSEUDOGENE = "pseudogene"
    NCRNA = "ncRNA"
    UNKNOWN = "unknown"


class GeneModel(Base):
    """
    SQLAlchemy Gene model with database constraints and relationships.

    Represents a gene in the MED13 knowledge base with all
    necessary metadata and database relationships.
    """

    __tablename__ = "genes"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Primary identifiers - unique constraints
    gene_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    # Descriptive fields
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    gene_type: Mapped[str] = mapped_column(
        String(20),
        default="unknown",
        nullable=False,
    )

    # Genomic location
    chromosome: Mapped[str | None] = mapped_column(String(10), nullable=True)
    start_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # External identifiers - with appropriate constraints
    ensembl_id: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )
    ncbi_gene_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )
    uniprot_id: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )

    # Relationships
    variants: Mapped[list["VariantModel"]] = relationship(back_populates="gene")

    # Audit fields inherited from Base

    __table_args__ = {  # noqa: RUF012
        "sqlite_autoincrement": True,  # Ensure SQLite autoincrement works properly
    }
