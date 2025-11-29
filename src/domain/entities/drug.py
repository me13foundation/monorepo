"""
Drug entity for MED13 Resource Library.

Represents therapeutic agents (small molecules, ASOs, etc.) that may
modulate MED13 function or downstream pathways.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DrugApprovalStatus(str, Enum):
    APPROVED = "approved"
    INVESTIGATIONAL = "investigational"
    WITHDRAWN = "withdrawn"
    EXPERIMENTAL = "experimental"


class TherapeuticModality(str, Enum):
    SMALL_MOLECULE = "small_molecule"
    ASO = "antisense_oligonucleotide"
    GENE_THERAPY = "gene_therapy"
    CRISPR = "crispr_editing"
    ANTIBODY = "antibody"
    OTHER = "other"


class Drug(BaseModel):
    """
    Represents a therapeutic candidate or approved drug.
    """

    id: str  # Primary ID (e.g., DrugBank ID, PubChem CID)
    name: str
    synonyms: list[str] = Field(default_factory=list)

    # Therapeutic Properties
    modality: TherapeuticModality = TherapeuticModality.SMALL_MOLECULE
    mechanism_of_action: str | None = None
    targets: list[str] = Field(default_factory=list)  # List of Target Gene Symbols

    # Clinical Status
    approval_status: DrugApprovalStatus = DrugApprovalStatus.EXPERIMENTAL
    is_fda_approved: bool = False

    # Critical attributes for Neurodevelopmental Disorders
    brain_penetrant: bool | None = None
    safety_profile: str | None = None

    # Metadata
    source: str = "manual_curation"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore",
    )
