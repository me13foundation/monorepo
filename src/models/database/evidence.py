"""
Evidence SQLAlchemy model for MED13 Resource Library.
Database representation of supporting evidence for variant-phenotype relationships.
"""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, Float, Enum as SQLEnum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .variant import VariantModel
    from .phenotype import PhenotypeModel
    from .publication import PublicationModel


class EvidenceLevel(SQLEnum):
    """Evidence confidence level classification."""

    DEFINITIVE = "definitive"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"
    WEAK = "weak"
    DISPROVEN = "disproven"


class EvidenceType(SQLEnum):
    """Type of evidence supporting the association."""

    CLINICAL_REPORT = "clinical_report"
    FUNCTIONAL_STUDY = "functional_study"
    ANIMAL_MODEL = "animal_model"
    BIOCHEMICAL = "biochemical"
    COMPUTATIONAL = "computational"
    LITERATURE_REVIEW = "literature_review"
    EXPERT_OPINION = "expert_opinion"


class EvidenceModel(Base):
    """
    SQLAlchemy Evidence model for variant-phenotype associations.

    Represents supporting evidence in the MED13 knowledge base with
    confidence levels, citations, and relationships.
    """

    __tablename__ = "evidence"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phenotype_id: Mapped[int] = mapped_column(
        ForeignKey("phenotypes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    publication_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("publications.id", ondelete="SET NULL"), index=True
    )

    # Evidence classification
    evidence_level: Mapped[str] = mapped_column(
        String(20), default="supporting", nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(
        String(30), default="literature_review", nullable=False
    )

    # Evidence content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Confidence and scoring
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    quality_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1-10 scale

    # Study details
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    study_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    statistical_significance: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Review status
    reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)
    review_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    variant: Mapped["VariantModel"] = relationship(back_populates="evidence")
    phenotype: Mapped["PhenotypeModel"] = relationship(back_populates="evidence")
    publication: Mapped[Optional["PublicationModel"]] = relationship(
        back_populates="evidence"
    )

    __table_args__ = {
        "sqlite_autoincrement": True,
    }
