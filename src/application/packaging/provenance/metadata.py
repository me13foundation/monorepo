"""
Metadata enrichment for FAIR packaging.

Enhances dataset metadata with provenance information,
licensing details, and FAIR compliance annotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypedDict, Unpack, cast

if TYPE_CHECKING:
    from src.models.value_objects.provenance import Provenance
    from src.type_definitions.common import JSONObject, JSONValue


class DatasetMetadataOptions(TypedDict, total=False):
    """Optional keyword arguments accepted by DatasetMetadata."""

    contributors: list[JSONObject]
    keywords: list[str]
    date_created: datetime | None
    date_modified: datetime | None
    date_published: datetime | None
    temporal_coverage: JSONObject | None
    spatial_coverage: JSONObject | None
    license_url: str | None
    rights_statement: str | None
    access_rights: str
    conforms_to: list[str]
    encoding_format: str | None
    compression_format: str | None
    byte_size: int | None
    provenance: Provenance | None


@dataclass
class DatasetMetadata:
    """Enhanced metadata for FAIR dataset packaging."""

    # Core metadata
    title: str
    description: str
    creators: list[JSONObject] = field(default_factory=list)
    contributors: list[JSONObject] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    # Temporal metadata
    date_created: datetime | None = None
    date_modified: datetime | None = None
    date_published: datetime | None = None
    temporal_coverage: JSONObject | None = None

    # Spatial metadata
    spatial_coverage: JSONObject | None = None

    # Licensing and rights
    license_url: str | None = None
    rights_statement: str | None = None
    access_rights: str = "public"

    # FAIR metadata
    conforms_to: list[str] = field(
        default_factory=lambda: [
            "https://w3id.org/ro/crate/1.1",
            "https://www.go-fair.org/fair-principles/",
        ],
    )

    # Technical metadata
    encoding_format: str | None = None
    compression_format: str | None = None
    byte_size: int | None = None

    # Provenance metadata
    provenance: Provenance | None = None

    def to_ro_crate_metadata(self) -> JSONObject:
        """Convert to RO-Crate metadata format."""
        metadata: JSONObject = {
            "@context": ["https://w3id.org/ro/crate/1.1/context", {"@base": None}],
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
                    "about": {"@id": "./"},
                },
                {
                    "@id": "./",
                    "@type": ["Dataset"],
                    "name": self.title,
                    "description": self.description,
                    "dateCreated": (
                        self.date_created.isoformat() if self.date_created else None
                    ),
                    "dateModified": (
                        self.date_modified.isoformat() if self.date_modified else None
                    ),
                    "datePublished": (
                        self.date_published.isoformat() if self.date_published else None
                    ),
                    "keywords": cast("list[JSONValue]", self.keywords),
                    "conformsTo": cast(
                        "list[JSONValue]",
                        [{"@id": standard} for standard in self.conforms_to],
                    ),
                },
            ],
        }

        graph_nodes = cast("list[JSONObject]", metadata["@graph"])

        # Add creators
        if self.creators:
            graph_nodes[1]["creator"] = cast("list[JSONValue]", self.creators)

        # Add license
        if self.license_url:
            graph_nodes[1]["license"] = cast(
                "JSONObject",
                {"@id": self.license_url},
            )

        return metadata

    def enrich_with_provenance(self, provenance: Provenance) -> None:
        """Enrich metadata with provenance information."""
        self.provenance = provenance

        # Update temporal information
        if provenance.acquired_at:
            if not self.date_created:
                self.date_created = provenance.acquired_at
            if not self.date_modified:
                self.date_modified = provenance.acquired_at

        # Add processing information to description
        if provenance.processing_steps:
            processing_info = (
                f"\n\nData Processing: {'; '.join(provenance.processing_steps)}"
            )
            self.description += processing_info

    def add_fair_compliance_info(self) -> None:
        """Add FAIR compliance information to metadata."""
        fair_info = """
        This dataset follows FAIR principles:
        - Findable: DOI and persistent identifiers
        - Accessible: Open access via standard protocols
        - Interoperable: Uses standard formats and vocabularies
        - Reusable: Clear licensing and usage guidelines
        """

        self.description += fair_info

        # Add FAIR-related keywords
        fair_keywords = ["FAIR", "Open Data", "Biomedical", "Research Data"]
        for keyword in fair_keywords:
            if keyword not in self.keywords:
                self.keywords.append(keyword)


class MetadataEnricher:
    """Service for enriching dataset metadata."""

    def __init__(self) -> None:
        self.templates: dict[str, DatasetMetadata] = {}

    def create_base_metadata(
        self,
        title: str,
        description: str,
        creators: list[JSONObject],
        **kwargs: Unpack[DatasetMetadataOptions],
    ) -> DatasetMetadata:
        """Create base metadata with standard FAIR fields."""
        metadata = DatasetMetadata(
            title=title,
            description=description,
            creators=creators,
            **kwargs,
        )

        # Add FAIR compliance info
        metadata.add_fair_compliance_info()

        return metadata

    def enrich_for_publication(
        self,
        metadata: DatasetMetadata,
        doi: str | None = None,
        publication_date: datetime | None = None,
    ) -> DatasetMetadata:
        """Enrich metadata for publication."""
        metadata.date_published = publication_date or datetime.now(UTC)

        if doi:
            # Add DOI as identifier
            metadata.conforms_to.append("https://www.doi.org/")
            # Could add DOI-specific metadata here

        return metadata

    def validate_metadata_completeness(self, metadata: DatasetMetadata) -> list[str]:
        """Validate that metadata meets minimum completeness requirements."""
        issues = []

        # Required fields
        if not metadata.title:
            issues.append("Title is required")
        if not metadata.description:
            issues.append("Description is required")
        if not metadata.creators:
            issues.append("At least one creator is required")
        if not metadata.license_url:
            issues.append("License URL is required")

        # FAIR compliance checks
        if not any("doi.org" in conform for conform in metadata.conforms_to):
            issues.append("DOI standard should be referenced")

        return issues


__all__ = ["DatasetMetadata", "DatasetMetadataOptions", "MetadataEnricher"]
