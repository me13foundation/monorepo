"""
Evidence SQLAlchemy model for MED13 Resource Library.
Database representation of supporting evidence for variant-phenotype relationships.
"""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .phenotype import PhenotypeModel
    from .publication import PublicationModel
    from .variant import VariantModel


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
        ForeignKey("variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phenotype_id: Mapped[int] = mapped_column(
        ForeignKey("phenotypes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    publication_id: Mapped[int | None] = mapped_column(
        ForeignKey("publications.id", ondelete="SET NULL"),
        index=True,
    )

    # Evidence classification
    evidence_level: Mapped[str] = mapped_column(
        String(20),
        default="supporting",
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(
        String(30),
        default="literature_review",
        nullable=False,
    )

    # Evidence content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Confidence and scoring
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    quality_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )  # 1-10 scale

    # Study details
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    study_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    statistical_significance: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Review status
    reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    variant: Mapped["VariantModel"] = relationship(back_populates="evidence")
    phenotype: Mapped["PhenotypeModel"] = relationship(back_populates="evidence")
    publication: Mapped[Optional["PublicationModel"]] = relationship(
        back_populates="evidence",
    )

    __table_args__ = {"sqlite_autoincrement": True}  # noqa: RUF012
