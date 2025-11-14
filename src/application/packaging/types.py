"""
Shared TypedDict definitions for packaging and provenance modules.

These structures ensure JSON metadata exchanged between builders,
serializers, and validators remains type-safe without relying on untyped helpers.
"""

from __future__ import annotations

from typing import TypedDict


class ROCrateFileEntryRequired(TypedDict):
    """Required fields for a RO-Crate file entry."""

    path: str


class ROCrateFileEntry(ROCrateFileEntryRequired, total=False):
    """File metadata published within the RO-Crate."""

    name: str
    description: str
    encodingFormat: str
    dateCreated: str


ProvenanceSourceEntry = TypedDict(
    "ProvenanceSourceEntry",
    {
        "@type": str,  # noqa: A003 - JSON-LD field name
        "name": str,
        "url": str,
        "contentUrl": str,
        "datePublished": str,
        "version": str,
        "processingSteps": list[str],
        "qualityScore": float,
        "validationStatus": str,
    },
    total=False,
)


class ProvenanceMetadata(TypedDict, total=False):
    """Collection of provenance sources included in metadata exports."""

    sources: list[ProvenanceSourceEntry]


class LicenseSourceEntry(TypedDict, total=False):
    """License information for an upstream data source."""

    source: str
    license: str


class LicenseManifest(TypedDict, total=False):
    """Structure of ``license-manifest.yml`` documents."""

    package_license: str
    sources: list[LicenseSourceEntry]
