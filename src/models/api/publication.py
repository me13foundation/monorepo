"""
Publication API schemas for MED13 Resource Library.

Pydantic models for publication-related API requests and responses.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class PublicationType(str, Enum):
    """Publication type classification."""

    JOURNAL_ARTICLE = "journal_article"
    REVIEW_ARTICLE = "review_article"
    CASE_REPORT = "case_report"
    CONFERENCE_ABSTRACT = "conference_abstract"
    BOOK_CHAPTER = "book_chapter"
    THESIS = "thesis"
    PREPRINT = "preprint"


class AuthorInfo(BaseModel):
    """Schema for author information."""

    name: str = Field(..., description="Full author name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    affiliation: Optional[str] = Field(None, description="Author affiliation")
    orcid: Optional[str] = Field(
        None, pattern=r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", description="ORCID identifier"
    )


class PublicationCreate(BaseModel):
    """
    Schema for creating new publications.

    Requires essential citation information.
    """

    model_config = ConfigDict(strict=True)

    # Required fields
    title: str = Field(..., description="Publication title")
    authors: List[AuthorInfo] = Field(..., min_length=1, description="List of authors")
    journal: str = Field(..., max_length=200, description="Journal name")
    publication_year: int = Field(..., ge=1900, le=2100, description="Publication year")

    # Optional identifiers
    pubmed_id: Optional[str] = Field(None, max_length=20, description="PubMed ID")
    pmc_id: Optional[str] = Field(None, max_length=20, description="PMC ID")
    doi: Optional[str] = Field(None, max_length=100, description="DOI")

    # Detailed citation
    volume: Optional[str] = Field(None, max_length=20, description="Journal volume")
    issue: Optional[str] = Field(None, max_length=20, description="Journal issue")
    pages: Optional[str] = Field(None, max_length=50, description="Page numbers")
    publication_date: Optional[date] = Field(None, description="Full publication date")

    # Content
    publication_type: PublicationType = Field(
        default=PublicationType.JOURNAL_ARTICLE, description="Publication type"
    )
    abstract: Optional[str] = Field(None, description="Publication abstract")
    keywords: Optional[List[str]] = Field(None, description="Keywords")

    # Quality metrics
    citation_count: Optional[int] = Field(None, ge=0, description="Citation count")
    impact_factor: Optional[float] = Field(
        None, ge=0, description="Journal impact factor"
    )

    # Review and access
    reviewed: bool = Field(
        default=False, description="Whether publication has been reviewed"
    )
    relevance_score: Optional[int] = Field(
        None, ge=1, le=5, description="MED13 relevance score (1-5)"
    )
    full_text_url: Optional[str] = Field(
        None, max_length=500, description="Full text URL"
    )
    open_access: bool = Field(default=False, description="Whether openly accessible")

    @field_validator("authors")
    @classmethod
    def validate_authors(cls, v: List[AuthorInfo]) -> List[AuthorInfo]:
        """Ensure at least one author is provided."""
        if not v:
            raise ValueError("At least one author is required")
        return v


class PublicationUpdate(BaseModel):
    """
    Schema for updating existing publications.

    All fields are optional for partial updates.
    """

    model_config = ConfigDict(strict=True)

    # Updatable identifiers
    pubmed_id: Optional[str] = Field(None, max_length=20)
    pmc_id: Optional[str] = Field(None, max_length=20)
    doi: Optional[str] = Field(None, max_length=100)

    # Content updates
    title: Optional[str] = None
    authors: Optional[List[AuthorInfo]] = Field(None, min_length=1)
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None

    # Citation updates
    volume: Optional[str] = Field(None, max_length=20)
    issue: Optional[str] = Field(None, max_length=20)
    pages: Optional[str] = Field(None, max_length=50)
    publication_date: Optional[date] = None

    # Quality metrics
    citation_count: Optional[int] = Field(None, ge=0)
    impact_factor: Optional[float] = Field(None, ge=0)

    # Review and access
    reviewed: Optional[bool] = None
    relevance_score: Optional[int] = Field(None, ge=1, le=5)
    full_text_url: Optional[str] = Field(None, max_length=500)
    open_access: Optional[bool] = None


class PublicationResponse(BaseModel):
    """
    Complete publication response schema for API endpoints.

    Includes all publication data plus computed fields and relationships.
    """

    model_config = ConfigDict(strict=True, from_attributes=True)

    # Primary identifiers
    id: int = Field(..., description="Database primary key")
    pubmed_id: Optional[str] = Field(None, description="PubMed ID")
    pmc_id: Optional[str] = Field(None, description="PMC ID")
    doi: Optional[str] = Field(None, description="DOI")

    # Citation information
    title: str = Field(..., description="Publication title")
    authors: List[AuthorInfo] = Field(..., description="List of authors")
    journal: str = Field(..., description="Journal name")
    publication_year: int = Field(..., description="Publication year")

    # Detailed citation
    volume: Optional[str] = Field(None, description="Journal volume")
    issue: Optional[str] = Field(None, description="Journal issue")
    pages: Optional[str] = Field(None, description="Page numbers")
    publication_date: Optional[date] = Field(None, description="Full publication date")

    # Content
    publication_type: PublicationType = Field(..., description="Publication type")
    abstract: Optional[str] = Field(None, description="Publication abstract")
    keywords: Optional[List[str]] = Field(None, description="Keywords")

    # Quality metrics
    citation_count: Optional[int] = Field(None, description="Citation count")
    impact_factor: Optional[float] = Field(None, description="Journal impact factor")

    # Review and access
    reviewed: bool = Field(..., description="Whether publication has been reviewed")
    relevance_score: Optional[int] = Field(
        None, ge=1, le=5, description="MED13 relevance score (1-5)"
    )
    full_text_url: Optional[str] = Field(None, description="Full text URL")
    open_access: bool = Field(..., description="Whether openly accessible")

    # Metadata
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Computed fields
    evidence_count: int = Field(
        default=0, description="Number of associated evidence records"
    )

    # Optional relationships (included based on query parameters)
    evidence: Optional[List[Dict[str, Any]]] = Field(
        None, description="Associated evidence"
    )


# Type aliases for API documentation
PublicationList = List[PublicationResponse]
