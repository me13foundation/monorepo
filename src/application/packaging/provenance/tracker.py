"""
Provenance tracking utilities for packaging.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List
from pathlib import Path
import json

from src.models.value_objects.provenance import Provenance


class ProvenanceTracker:
    """Track and serialize provenance information."""

    @staticmethod
    def serialize_provenance(
        provenance_records: List[Provenance],
    ) -> Dict[str, Any]:
        """
        Serialize provenance records to JSON-LD format.

        Args:
            provenance_records: List of Provenance value objects

        Returns:
            Serialized provenance dictionary
        """
        sources = []

        for prov in provenance_records:
            source_info = {
                "@type": "DataDownload",
                "name": prov.source.value,
                "datePublished": (
                    prov.acquired_at.isoformat()
                    if prov.acquired_at
                    else datetime.now(UTC).isoformat()
                ),
            }

            if prov.source_url:
                source_info["url"] = prov.source_url

            if prov.source_version:
                source_info["version"] = prov.source_version

            if prov.processing_steps:
                source_info["processingSteps"] = prov.processing_steps

            if prov.quality_score is not None:
                source_info["qualityScore"] = prov.quality_score

            if prov.validation_status:
                source_info["validationStatus"] = prov.validation_status

            sources.append(source_info)

        return {"sources": sources}

    @staticmethod
    def write_provenance_metadata(
        provenance_records: List[Provenance],
        output_path: Path,
    ) -> None:
        """
        Write provenance metadata to file.

        Args:
            provenance_records: List of Provenance value objects
            output_path: Path to write metadata file
        """
        metadata = ProvenanceTracker.serialize_provenance(provenance_records)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    @staticmethod
    def enrich_with_provenance(
        metadata: Dict[str, Any],
        provenance_records: List[Provenance],
    ) -> Dict[str, Any]:
        """
        Enrich metadata dictionary with provenance information.

        Args:
            metadata: Existing metadata dictionary
            provenance_records: List of Provenance value objects

        Returns:
            Enriched metadata dictionary
        """
        provenance_info = ProvenanceTracker.serialize_provenance(provenance_records)

        if "@graph" in metadata:
            # Find root dataset
            for entity in metadata["@graph"]:
                if entity.get("@id") == "./":
                    if "hasPart" not in entity:
                        entity["hasPart"] = []
                    entity["hasPart"].extend(provenance_info["sources"])
                    break

        return metadata
