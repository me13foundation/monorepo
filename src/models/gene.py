"""
Gene models for MED13 Resource Library.
Strongly typed Pydantic models with comprehensive validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo
from enum import Enum


class GeneType(str, Enum):
    """Gene type classification."""

    PROTEIN_CODING = "protein_coding"
    PSEUDOGENE = "pseudogene"
    NCRNA = "ncRNA"
    UNKNOWN = "unknown"


class Gene(BaseModel):
    """
    Core Gene model with strict validation.

    Represents a gene in the MED13 knowledge base with all
    necessary metadata and validation rules.
    """

    model_config = ConfigDict(strict=True, from_attributes=True)

    # Primary identifiers
    gene_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Z0-9_-]+$",
        description="Unique gene identifier",
    )
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        pattern=r"^[A-Z0-9_-]+$",
        description="Official gene symbol",
    )

    # Descriptive fields
    name: Optional[str] = Field(None, max_length=200, description="Full gene name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Gene description"
    )

    # Classification
    gene_type: GeneType = Field(default=GeneType.UNKNOWN, description="Type of gene")

    # Genomic location
    chromosome: Optional[str] = Field(
        None, pattern=r"^(chr)?[0-9XYM]+$", description="Chromosome location"
    )
    start_position: Optional[int] = Field(
        None, ge=1, description="Start position on chromosome"
    )
    end_position: Optional[int] = Field(
        None, ge=1, description="End position on chromosome"
    )

    # External identifiers
    ensembl_id: Optional[str] = Field(
        None, pattern=r"^ENSG[0-9]+$", description="Ensembl gene ID"
    )
    ncbi_gene_id: Optional[int] = Field(None, ge=1, description="NCBI Gene ID")
    uniprot_id: Optional[str] = Field(
        None, pattern=r"^[A-Z0-9_-]+$", description="UniProt accession"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    # Validation methods
    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Ensure gene symbol is uppercase."""
        return v.upper()

    @field_validator("end_position")
    @classmethod
    def validate_positions(
        cls, v: Optional[int], info: ValidationInfo
    ) -> Optional[int]:
        """Ensure end position is after start position."""
        if v is not None:
            start_pos = info.data.get("start_position")
            if start_pos is not None and v < start_pos:
                raise ValueError("end_position must be greater than start_position")
        return v

    @field_validator("updated_at")
    @classmethod
    def validate_timestamps(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Ensure updated_at is not before created_at."""
        created_at = info.data.get("created_at")
        if created_at and v < created_at:
            raise ValueError("updated_at cannot be before created_at")
        return v


class GeneCreate(BaseModel):
    """
    Model for creating new genes.
    Excludes auto-generated fields like timestamps and IDs.
    """

    model_config = ConfigDict(strict=True)

    symbol: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Z0-9_-]+$")
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    gene_type: GeneType = Field(default=GeneType.UNKNOWN)
    chromosome: Optional[str] = Field(None, pattern=r"^(chr)?[0-9XYM]+$")
    start_position: Optional[int] = Field(None, ge=1)
    end_position: Optional[int] = Field(None, ge=1)
    ensembl_id: Optional[str] = Field(None, pattern=r"^ENSG[0-9]+$")
    ncbi_gene_id: Optional[int] = Field(None, ge=1)
    uniprot_id: Optional[str] = Field(None, pattern=r"^[A-Z0-9_-]+$")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        return v.upper()

    @field_validator("end_position")
    @classmethod
    def validate_positions(
        cls, v: Optional[int], info: ValidationInfo
    ) -> Optional[int]:
        if v is not None:
            start_pos = info.data.get("start_position")
            if start_pos is not None and v < start_pos:
                raise ValueError("end_position must be greater than start_position")
        return v


class GeneResponse(Gene):
    """
    Response model for API endpoints.
    Includes computed fields and relationships.
    """

    model_config = ConfigDict(strict=True, from_attributes=True)

    # Computed fields
    variant_count: int = Field(default=0, description="Number of associated variants")
    phenotype_count: int = Field(
        default=0, description="Number of associated phenotypes"
    )

    # Optional relationships (can be included based on query parameters)
    variants: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Associated variants (optional)"
    )
    phenotypes: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Associated phenotypes (optional)"
    )


# Type aliases for better API documentation
GeneList = List[GeneResponse]
GeneCreateRequest = GeneCreate
GeneUpdateRequest = GeneCreate  # Same fields for updates
