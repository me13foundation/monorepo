"""
Bulk Export Service for MED13 Resource Library.

Handles large dataset serialization and streaming export capabilities.
"""

import csv
import gzip
import json
from enum import Enum
from io import StringIO
from typing import Any, Dict, Generator, List, Optional, Union

from src.application.services.gene_service import GeneApplicationService
from src.application.services.variant_service import VariantApplicationService
from src.application.services.phenotype_service import PhenotypeApplicationService
from src.application.services.evidence_service import EvidenceApplicationService


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    CSV = "csv"
    TSV = "tsv"
    JSONL = "jsonl"  # JSON Lines format


class CompressionFormat(str, Enum):
    """Supported compression formats."""

    NONE = "none"
    GZIP = "gzip"


class BulkExportService:
    """
    Service for bulk data export with streaming and multiple format support.

    Handles large dataset serialization efficiently to avoid memory issues.
    """

    def __init__(
        self,
        gene_service: GeneApplicationService,
        variant_service: VariantApplicationService,
        phenotype_service: PhenotypeApplicationService,
        evidence_service: EvidenceApplicationService,
    ):
        """
        Initialize the bulk export service.

        Args:
            gene_service: Gene application service
            variant_service: Variant application service
            phenotype_service: Phenotype application service
            evidence_service: Evidence application service
        """
        self._gene_service = gene_service
        self._variant_service = variant_service
        self._phenotype_service = phenotype_service
        self._evidence_service = evidence_service

    def export_data(
        self,
        entity_type: str,
        export_format: ExportFormat,
        compression: CompressionFormat = CompressionFormat.NONE,
        filters: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
    ) -> Generator[Union[str, bytes], None, None]:
        """
        Export data for a specific entity type in the requested format.

        Args:
            entity_type: Type of entity to export ('genes', 'variants', 'phenotypes', 'evidence')
            export_format: Format for export (JSON, CSV, TSV, JSONL)
            compression: Compression format (NONE or GZIP)
            filters: Optional filters to apply to the data
            chunk_size: Number of records to process at once

        Yields:
            Chunks of data as strings (or bytes for compressed output)
        """
        if entity_type == "genes":
            yield from self._export_genes(
                export_format, compression, filters, chunk_size
            )
        elif entity_type == "variants":
            yield from self._export_variants(
                export_format, compression, filters, chunk_size
            )
        elif entity_type == "phenotypes":
            yield from self._export_phenotypes(
                export_format, compression, filters, chunk_size
            )
        elif entity_type == "evidence":
            yield from self._export_evidence(
                export_format, compression, filters, chunk_size
            )
        else:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    def _export_genes(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: Optional[Dict[str, Any]],
        chunk_size: int,
    ) -> Generator[Union[str, bytes], None, None]:
        """Export genes data."""
        # Get all genes (simplified - in production would use pagination)
        genes = self._gene_service.list_genes(
            page=1, per_page=10000, sort_by="symbol", sort_order="asc"
        )[0]  # Get just the genes list

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(genes, compression, "genes")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                genes, export_format, compression, self._get_gene_fields()
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(genes, compression)

    def _export_variants(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: Optional[Dict[str, Any]],
        chunk_size: int,
    ) -> Generator[Union[str, bytes], None, None]:
        """Export variants data."""
        variants = self._variant_service.list_variants(
            page=1,
            per_page=10000,
            sort_by="variant_id",
            sort_order="asc",
            filters=filters,
        )[0]  # Get just the variants list

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(variants, compression, "variants")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                variants, export_format, compression, self._get_variant_fields()
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(variants, compression)

    def _export_phenotypes(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: Optional[Dict[str, Any]],
        chunk_size: int,
    ) -> Generator[Union[str, bytes], None, None]:
        """Export phenotypes data."""
        phenotypes = self._phenotype_service.list_phenotypes(
            page=1, per_page=10000, sort_by="name", sort_order="asc", filters=filters
        )[0]  # Get just the phenotypes list

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(phenotypes, compression, "phenotypes")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                phenotypes, export_format, compression, self._get_phenotype_fields()
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(phenotypes, compression)

    def _export_evidence(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: Optional[Dict[str, Any]],
        chunk_size: int,
    ) -> Generator[Union[str, bytes], None, None]:
        """Export evidence data."""
        evidence_list = self._evidence_service.list_evidence(
            page=1,
            per_page=10000,
            sort_by="created_at",
            sort_order="asc",
            filters=filters,
        )[0]  # Get just the evidence list

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(evidence_list, compression, "evidence")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                evidence_list, export_format, compression, self._get_evidence_fields()
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(evidence_list, compression)

    def _export_as_json(
        self,
        items: List[Any],
        compression: CompressionFormat,
        entity_type: str,
    ) -> Generator[Union[str, bytes], None, None]:
        """Export data as JSON format."""
        data = {entity_type: [self._serialize_item(item) for item in items]}

        json_str = json.dumps(data, indent=2, default=str)

        if compression == CompressionFormat.GZIP:
            yield gzip.compress(json_str.encode("utf-8"))
        else:
            yield json_str

    def _export_as_jsonl(
        self,
        items: List[Any],
        compression: CompressionFormat,
    ) -> Generator[Union[str, bytes], None, None]:
        """Export data as JSON Lines format (one JSON object per line)."""
        lines = []
        for item in items:
            line = json.dumps(self._serialize_item(item), default=str)
            lines.append(line)

        content = "\n".join(lines)

        if compression == CompressionFormat.GZIP:
            yield gzip.compress(content.encode("utf-8"))
        else:
            yield content

    def _export_as_csv(
        self,
        items: List[Any],
        export_format: ExportFormat,
        compression: CompressionFormat,
        field_names: List[str],
    ) -> Generator[Union[str, bytes], None, None]:
        """Export data as CSV or TSV format."""
        delimiter = "\t" if export_format == ExportFormat.TSV else ","

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=field_names, delimiter=delimiter)

        # Write header
        writer.writeheader()

        # Write data rows
        for item in items:
            row = self._item_to_csv_row(item, field_names)
            writer.writerow(row)

        content = output.getvalue()

        if compression == CompressionFormat.GZIP:
            yield gzip.compress(content.encode("utf-8"))
        else:
            yield content

    def _serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize an entity item to a dictionary."""
        # Handle NamedTuple objects (test fixtures)
        if hasattr(item, "_fields"):
            # This is a NamedTuple
            result: Dict[str, Any] = {}
            for field in item._fields:
                value = getattr(item, field)
                if hasattr(value, "_fields") or hasattr(
                    value, "__dict__"
                ):  # Nested objects
                    result[field] = self._serialize_item(value)
                elif isinstance(value, (list, tuple)):
                    result[field] = [
                        (
                            self._serialize_item(v)
                            if (hasattr(v, "_fields") or hasattr(v, "__dict__"))
                            else v
                        )
                        for v in value
                    ]
                else:
                    result[field] = value
            return result
        # Handle regular objects with __dict__
        elif hasattr(item, "__dict__"):
            obj_result: Dict[str, Any] = {}
            for key, value in item.__dict__.items():
                if not key.startswith("_"):  # Skip private attributes
                    if hasattr(value, "__dict__") or hasattr(
                        value, "_fields"
                    ):  # Handle nested objects
                        obj_result[key] = self._serialize_item(value)
                    elif isinstance(value, (list, tuple)):
                        obj_result[key] = [
                            (
                                self._serialize_item(v)
                                if (hasattr(v, "__dict__") or hasattr(v, "_fields"))
                                else v
                            )
                            for v in value
                        ]
                    else:
                        obj_result[key] = value
            return obj_result
        elif isinstance(item, dict):
            return item
        else:
            return {"value": item}

    def _item_to_csv_row(self, item: Any, field_names: List[str]) -> Dict[str, Any]:
        """Convert an item to a CSV row dictionary."""
        serialized = self._serialize_item(item)
        row = {}

        for field in field_names:
            value = serialized.get(field, "")
            # Handle nested fields with dot notation (e.g., 'identifier.hpo_id')
            if "." in field:
                parts = field.split(".")
                current = serialized
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part, "")
                    elif hasattr(current, part):
                        current = getattr(current, part, "")
                    else:
                        current = ""
                        break  # type: ignore[unreachable]
                value = current
            # Continue with the rest of the field processing

            # Convert complex types to strings
            if isinstance(value, (list, tuple)):
                value = ";".join(str(v) for v in value)
            elif value is None:
                value = ""
            else:
                value = str(value)

            row[field] = value

        return row

    def _get_gene_fields(self) -> List[str]:
        """Get field names for gene CSV export."""
        return [
            "id",
            "gene_id",
            "symbol",
            "name",
            "description",
            "gene_type",
            "chromosome",
            "start_position",
            "end_position",
            "ensembl_id",
            "ncbi_gene_id",
            "uniprot_id",
            "created_at",
            "updated_at",
        ]

    def _get_variant_fields(self) -> List[str]:
        """Get field names for variant CSV export."""
        return [
            "id",
            "variant_id",
            "clinvar_id",
            "chromosome",
            "position",
            "reference_allele",
            "alternate_allele",
            "variant_type",
            "clinical_significance",
            "gene_symbol",
            "hgvs_genomic",
            "hgvs_cdna",
            "hgvs_protein",
            "condition",
            "review_status",
            "allele_frequency",
            "gnomad_af",
            "created_at",
            "updated_at",
        ]

    def _get_phenotype_fields(self) -> List[str]:
        """Get field names for phenotype CSV export."""
        return [
            "id",
            "identifier.hpo_id",
            "identifier.hpo_term",
            "name",
            "definition",
            "category",
            "parent_hpo_id",
            "is_root_term",
            "frequency_in_med13",
            "severity_score",
            "created_at",
            "updated_at",
        ]

    def _get_evidence_fields(self) -> List[str]:
        """Get field names for evidence CSV export."""
        return [
            "id",
            "variant_id",
            "phenotype_id",
            "description",
            "summary",
            "evidence_level",
            "evidence_type",
            "confidence.score",
            "quality_score",
            "sample_size",
            "study_type",
            "statistical_significance",
            "reviewed",
            "review_date",
            "reviewer_notes",
            "created_at",
            "updated_at",
        ]

    def get_export_info(self, entity_type: str) -> Dict[str, Any]:
        """
        Get information about available export formats and entity counts.

        Args:
            entity_type: Type of entity

        Returns:
            Dictionary with export format options and entity statistics
        """
        # This would query the repositories for actual counts
        # For now, return static information
        return {
            "entity_type": entity_type,
            "supported_formats": [fmt.value for fmt in ExportFormat],
            "supported_compression": [comp.value for comp in CompressionFormat],
            "estimated_record_count": 0,  # Would be populated from repository
            "last_updated": None,  # Would track when data was last updated
        }


__all__ = ["BulkExportService", "ExportFormat", "CompressionFormat"]
