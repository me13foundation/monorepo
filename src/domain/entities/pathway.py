"""
Pathway entity for MED13 Resource Library.

Represents biological pathways and functional networks that MED13 regulates
or interacts with (e.g., Wnt signaling, Mitochondrial metabolism).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Pathway(BaseModel):
    """
    Represents a biological pathway or gene set.
    """

    id: str  # Reactome ID, GO ID, or Internal ID
    name: str
    source: str  # e.g., "Reactome", "GO", "KEGG", "WikiPathways"

    description: str | None = None

    # Graph Connectivity
    genes: list[str] = Field(
        default_factory=list,
    )  # List of Gene Symbols in this pathway
    parent_pathways: list[str] = Field(default_factory=list)  # IDs of parent pathways

    # Functional Category
    category: Literal[
        "signaling",
        "metabolic",
        "regulatory",
        "disease",
        "other",
    ] = "other"

    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore",
    )
