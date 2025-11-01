"""
Evidence API schemas for MED13 Resource Library.

Pydantic models for evidence-related API requests and responses.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class EvidenceLevel(str, Enum):
    """Evidence confidence level classification."""

    DEFINITIVE = "definitive"
    STRONG = "strong"
    MODERATE = "moderate"
    SUPPORTING = "supporting"
    WEAK = "weak"
    DISPROVEN = "disproven"


class EvidenceType(str, Enum):
    """Type of evidence supporting the association."""

    CLINICAL_REPORT = "clinical_report"
    FUNCTIONAL_STUDY = "functional_study"
    ANIMAL_MODEL = "animal_model"
    BIOCHEMICAL = "biochemical"
    COMPUTATIONAL = "computational"
    LITERATURE_REVIEW = "literature_review"
    EXPERT_OPINION = "expert_opinion"


class EvidenceCreate(BaseModel):
    """
    Schema for creating new evidence records.

    Links variants to phenotypes with supporting evidence.
    """

    model_config = ConfigDict(strict=True)

    # Required relationships
    variant_id: str = Field(..., description="Associated variant identifier")
    phenotype_id: str = Field(..., description="Associated phenotype HPO ID")

    # Evidence content
    description: str = Field(..., description="Evidence description")
    summary: Optional[str] = Field(None, description="Brief summary")

    # Classification
    evidence_level: EvidenceLevel = Field(
        default=EvidenceLevel.SUPPORTING, description="Evidence level"
    )
    evidence_type: EvidenceType = Field(
        default=EvidenceType.LITERATURE_REVIEW, description="Evidence type"
    )

    # Optional publication
    publication_id: Optional[str] = Field(
        None, description="Associated publication identifier"
    )

    # Confidence and scoring
    confidence_score: float = Field(
        default=0.5, ge=0, le=1, description="Confidence score (0-1)"
    )
    quality_score: Optional[int] = Field(
        None, ge=1, le=10, description="Quality score (1-10)"
    )

    # Study details
    sample_size: Optional[int] = Field(None, ge=1, description="Sample size")
    study_type: Optional[str] = Field(None, max_length=100, description="Study type")
    statistical_significance: Optional[str] = Field(
        None, max_length=50, description="Statistical significance"
    )

    # Review information
    reviewed: bool = Field(
        default=False, description="Whether evidence has been reviewed"
    )
    review_date: Optional[date] = Field(None, description="Review date")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")


class EvidenceUpdate(BaseModel):
    """
    Schema for updating existing evidence records.

    All fields are optional for partial updates.
    """

    model_config = ConfigDict(strict=True)

    # Updatable content
    description: Optional[str] = None
    summary: Optional[str] = None

    # Classification
    evidence_level: Optional[EvidenceLevel] = None
    evidence_type: Optional[EvidenceType] = None

    # Publication
    publication_id: Optional[str] = None

    # Confidence and scoring
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    quality_score: Optional[int] = Field(None, ge=1, le=10)

    # Study details
    sample_size: Optional[int] = Field(None, ge=1)
    study_type: Optional[str] = Field(None, max_length=100)
    statistical_significance: Optional[str] = Field(None, max_length=50)

    # Review information
    reviewed: Optional[bool] = None
    review_date: Optional[date] = None
    reviewer_notes: Optional[str] = None


class EvidenceResponse(BaseModel):
    """
    Complete evidence response schema for API endpoints.

    Includes all evidence data plus computed fields and relationships.
    """

    model_config = ConfigDict(strict=True, from_attributes=True)

    # Primary identifiers
    id: int = Field(..., description="Database primary key")

    # Relationships
    variant_id: str = Field(..., description="Associated variant identifier")
    phenotype_id: str = Field(..., description="Associated phenotype HPO ID")
    publication_id: Optional[str] = Field(
        None, description="Associated publication identifier"
    )

    # Evidence content
    description: str = Field(..., description="Evidence description")
    summary: Optional[str] = Field(None, description="Brief summary")

    # Classification
    evidence_level: EvidenceLevel = Field(..., description="Evidence level")
    evidence_type: EvidenceType = Field(..., description="Evidence type")

    # Confidence and scoring
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    quality_score: Optional[int] = Field(
        None, ge=1, le=10, description="Quality score (1-10)"
    )

    # Study details
    sample_size: Optional[int] = Field(None, description="Sample size")
    study_type: Optional[str] = Field(None, description="Study type")
    statistical_significance: Optional[str] = Field(
        None, description="Statistical significance"
    )

    # Review information
    reviewed: bool = Field(..., description="Whether evidence has been reviewed")
    review_date: Optional[date] = Field(None, description="Review date")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")

    # Metadata
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Optional relationships (included based on query parameters)
    variant: Optional[Dict[str, Any]] = Field(None, description="Variant details")
    phenotype: Optional[Dict[str, Any]] = Field(None, description="Phenotype details")
    publication: Optional[Dict[str, Any]] = Field(
        None, description="Publication details"
    )


# Type aliases for API documentation
EvidenceList = List[EvidenceResponse]
