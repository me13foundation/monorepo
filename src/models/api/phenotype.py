"""
Phenotype API schemas for MED13 Resource Library.

Pydantic models for phenotype-related API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PhenotypeCategory(str, Enum):
    """Phenotype category classification."""

    CONGENITAL = "congenital"
    DEVELOPMENTAL = "developmental"
    NEUROLOGICAL = "neurological"
    CARDIOVASCULAR = "cardiovascular"
    MUSCULOSKELETAL = "musculoskeletal"
    ENDOCRINE = "endocrine"
    IMMUNOLOGICAL = "immunological"
    ONCOLOGICAL = "oncological"
    OTHER = "other"


class PhenotypeCreate(BaseModel):
    """
    Schema for creating new phenotypes.

    Requires HPO identifier and basic phenotype information.
    """

    model_config = ConfigDict(strict=True)

    # Required HPO fields
    hpo_id: str = Field(..., pattern=r"^HP:\d{7}$", description="HPO identifier")
    hpo_term: str = Field(..., max_length=200, description="HPO term")
    name: str = Field(..., max_length=200, description="Phenotype name")

    # Optional fields
    definition: str | None = Field(None, description="Phenotype definition")
    synonyms: list[str] | None = Field(None, description="Alternative names")

    # Classification
    category: PhenotypeCategory = Field(
        default=PhenotypeCategory.OTHER,
        description="Phenotype category",
    )

    # HPO hierarchy
    parent_hpo_id: str | None = Field(
        None,
        pattern=r"^HP:\d{7}$",
        description="Parent HPO term",
    )
    is_root_term: bool = Field(default=False, description="Whether this is a root term")

    # Clinical context
    frequency_in_med13: str | None = Field(
        None,
        max_length=100,
        description="Frequency in MED13",
    )
    severity_score: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Severity score (1-5)",
    )


class PhenotypeUpdate(BaseModel):
    """
    Schema for updating existing phenotypes.

    All fields are optional for partial updates.
    """

    model_config = ConfigDict(strict=True)

    # Updatable fields
    name: str | None = Field(None, max_length=200)
    definition: str | None = Field(None)
    synonyms: list[str] | None = Field(None)
    category: PhenotypeCategory | None = None
    parent_hpo_id: str | None = Field(None, pattern=r"^HP:\d{7}$")
    is_root_term: bool | None = None
    frequency_in_med13: str | None = Field(None, max_length=100)
    severity_score: int | None = Field(None, ge=1, le=5)


class PhenotypeResponse(BaseModel):
    """
    Complete phenotype response schema for API endpoints.

    Includes all phenotype data plus computed fields and relationships.
    """

    model_config = ConfigDict(strict=True, from_attributes=True)

    # Primary identifiers
    id: int = Field(..., description="Database primary key")
    hpo_id: str = Field(..., description="HPO identifier")
    hpo_term: str = Field(..., description="HPO term")

    # Phenotype information
    name: str = Field(..., description="Phenotype name")
    definition: str | None = Field(None, description="Phenotype definition")
    synonyms: list[str] | None = Field(None, description="Alternative names")

    # Classification
    category: PhenotypeCategory = Field(..., description="Phenotype category")

    # HPO hierarchy
    parent_hpo_id: str | None = Field(None, description="Parent HPO term")
    is_root_term: bool = Field(..., description="Whether this is a root term")

    # Clinical context
    frequency_in_med13: str | None = Field(None, description="Frequency in MED13")
    severity_score: int | None = Field(
        None,
        ge=1,
        le=5,
        description="Severity score (1-5)",
    )

    # Metadata
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Computed fields
    evidence_count: int = Field(
        default=0,
        description="Number of associated evidence records",
    )
    variant_count: int = Field(default=0, description="Number of associated variants")

    # Optional relationships (included based on query parameters)
    parent_phenotype: dict[str, Any] | None = Field(
        None,
        description="Parent phenotype details",
    )
    child_phenotypes: list[dict[str, Any]] | None = Field(
        None,
        description="Child phenotypes",
    )
    evidence: list[dict[str, Any]] | None = Field(
        None,
        description="Associated evidence",
    )


# Type aliases for API documentation
PhenotypeList = list[PhenotypeResponse]
