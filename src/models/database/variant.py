"""
Variant SQLAlchemy model for MED13 Resource Library.
Database representation of genetic variants with clinical significance.
"""

from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .gene import GeneModel
    from .evidence import EvidenceModel


class VariantType(SQLEnum):
    """Variant type classification."""

    SNV = "snv"  # Single nucleotide variant
    INDEL = "indel"  # Insertion/deletion
    CNV = "cnv"  # Copy number variation
    STRUCTURAL = "structural"  # Structural variant
    UNKNOWN = "unknown"


class ClinicalSignificance(SQLEnum):
    """ClinVar clinical significance classification."""

    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    CONFLICTING = "conflicting"
    NOT_PROVIDED = "not_provided"


class VariantModel(Base):
    """
    SQLAlchemy Variant model with HGVS notation and clinical data.

    Represents genetic variants in the MED13 knowledge base with
    clinical significance, HGVS notation, and relationships.
    """

    __tablename__ = "variants"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to gene
    gene_id: Mapped[int] = mapped_column(
        ForeignKey("genes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Variant identifiers
    variant_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    clinvar_id: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )

    # Genomic coordinates
    chromosome: Mapped[str] = mapped_column(String(10), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reference_allele: Mapped[str] = mapped_column(String(1000), nullable=False)
    alternate_allele: Mapped[str] = mapped_column(String(1000), nullable=False)

    # HGVS notation
    hgvs_genomic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hgvs_protein: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hgvs_cdna: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Classification
    variant_type: Mapped[str] = mapped_column(
        String(20), default="unknown", nullable=False
    )
    clinical_significance: Mapped[str] = mapped_column(
        String(50), default="not_provided", nullable=False
    )

    # Clinical information
    condition: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    review_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Population frequency data
    allele_frequency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gnomad_af: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    gene: Mapped["GeneModel"] = relationship(back_populates="variants")
    evidence: Mapped[List["EvidenceModel"]] = relationship(back_populates="variant")

    __table_args__ = {
        "sqlite_autoincrement": True,
    }
