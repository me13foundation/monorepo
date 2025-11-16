"""
Bulk Export Service for MED13 Resource Library.

Handles large dataset serialization and streaming export capabilities.
"""

import csv
import gzip
import json
from collections.abc import Callable, Generator, Sequence
from datetime import datetime
from enum import Enum
from io import StringIO
from typing import TypeVar

from src.application.services.evidence_service import EvidenceApplicationService
from src.application.services.gene_service import GeneApplicationService
from src.application.services.phenotype_service import PhenotypeApplicationService
from src.application.services.variant_service import VariantApplicationService
from src.type_definitions.common import (
    JSONObject,
    JSONValue,
    QueryFilters,
    clone_query_filters,
)


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


EntityItem = TypeVar("EntityItem")


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
        self._gene_service = gene_service
        self._variant_service = variant_service
        self._phenotype_service = phenotype_service
        self._evidence_service = evidence_service

    def export_data(
        self,
        entity_type: str,
        export_format: ExportFormat,
        compression: CompressionFormat = CompressionFormat.NONE,
        filters: QueryFilters | None = None,
        chunk_size: int = 1000,
    ) -> Generator[str | bytes, None, None]:
        if entity_type == "genes":
            yield from self._export_genes(
                export_format,
                compression,
                filters,
                chunk_size,
            )
        elif entity_type == "variants":
            yield from self._export_variants(
                export_format,
                compression,
                filters,
                chunk_size,
            )
        elif entity_type == "phenotypes":
            yield from self._export_phenotypes(
                export_format,
                compression,
                filters,
                chunk_size,
            )
        elif entity_type == "evidence":
            yield from self._export_evidence(
                export_format,
                compression,
                filters,
                chunk_size,
            )
        else:
            msg = f"Unsupported entity type: {entity_type}"
            raise ValueError(msg)

    def _export_genes(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes, None, None]:
        filters_payload = self._copy_filters(filters)
        search_value = filters_payload.get("search")
        search_term = search_value if isinstance(search_value, str) else None
        genes = self._collect_paginated(
            lambda page, size: self._gene_service.list_genes(
                page=page,
                per_page=size,
                sort_by="symbol",
                sort_order="asc",
                search=search_term,
            ),
            chunk_size,
        )

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(genes, compression, "genes")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                genes,
                export_format,
                compression,
                self._get_gene_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(genes, compression)

    def _export_variants(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes, None, None]:
        variants = self._collect_paginated(
            lambda page, size: self._variant_service.list_variants(
                page=page,
                per_page=size,
                sort_by="variant_id",
                sort_order="asc",
                filters=filters,
            ),
            chunk_size,
        )

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(variants, compression, "variants")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                variants,
                export_format,
                compression,
                self._get_variant_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(variants, compression)

    def _export_phenotypes(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes, None, None]:
        phenotypes = self._collect_paginated(
            lambda page, size: self._phenotype_service.list_phenotypes(
                page=page,
                per_page=size,
                sort_by="name",
                sort_order="asc",
                filters=filters,
            ),
            chunk_size,
        )

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(phenotypes, compression, "phenotypes")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                phenotypes,
                export_format,
                compression,
                self._get_phenotype_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(phenotypes, compression)

    def _export_evidence(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes, None, None]:
        evidence_list = self._collect_paginated(
            lambda page, size: self._evidence_service.list_evidence(
                page=page,
                per_page=size,
                sort_by="created_at",
                sort_order="asc",
                filters=filters,
            ),
            chunk_size,
        )

        if export_format == ExportFormat.JSON:
            yield from self._export_as_json(evidence_list, compression, "evidence")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from self._export_as_csv(
                evidence_list,
                export_format,
                compression,
                self._get_evidence_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from self._export_as_jsonl(evidence_list, compression)

    def _export_as_json(
        self,
        items: list[EntityItem],
        compression: CompressionFormat,
        entity_type: str,
    ) -> Generator[str | bytes, None, None]:
        serialized_items = [self._serialize_item(item) for item in items]
        data: JSONObject = {
            entity_type: serialized_items,
        }

        json_str = json.dumps(data, indent=2, default=str)

        if compression == CompressionFormat.GZIP:
            yield gzip.compress(json_str.encode("utf-8"))
        else:
            yield json_str

    def _export_as_jsonl(
        self,
        items: list[EntityItem],
        compression: CompressionFormat,
    ) -> Generator[str | bytes, None, None]:
        content_lines = [
            json.dumps(self._serialize_item(item), default=str) for item in items
        ]
        content = "\n".join(content_lines)

        if compression == CompressionFormat.GZIP:
            yield gzip.compress(content.encode("utf-8"))
        else:
            yield content

    def _export_as_csv(
        self,
        items: list[EntityItem],
        export_format: ExportFormat,
        compression: CompressionFormat,
        field_names: list[str],
    ) -> Generator[str | bytes, None, None]:
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

    def _collect_paginated(
        self,
        fetch_page: Callable[[int, int], tuple[list[EntityItem], int]],
        chunk_size: int,
    ) -> list[EntityItem]:
        page = 1
        results: list[EntityItem] = []
        batch_size = max(chunk_size, 1)

        while True:
            items, _total = fetch_page(page, batch_size)
            if not items:
                break
            results.extend(items)
            if len(items) < batch_size:
                break
            page += 1

        return results

    def _serialize_item(self, item: object) -> JSONValue:
        if isinstance(item, datetime):
            return item.isoformat()

        if self._is_namedtuple(item):
            return self._serialize_namedtuple(item)

        if isinstance(item, dict):
            return {key: self._serialize_item(value) for key, value in item.items()}

        if hasattr(item, "__dict__"):
            return self._serialize_object(item)

        if isinstance(item, (list, tuple)):
            return self._serialize_sequence(item)

        return self._coerce_scalar(item)

    @staticmethod
    def _is_namedtuple(candidate: object) -> bool:
        return hasattr(candidate, "_fields") and all(
            isinstance(field, str) for field in getattr(candidate, "_fields", [])
        )

    def _serialize_namedtuple(self, item: object) -> JSONObject:
        fields_attr = getattr(item, "_fields", ())
        if not isinstance(fields_attr, Sequence):
            return {}
        field_names = [str(field) for field in fields_attr]
        return {
            field: self._serialize_item(getattr(item, field)) for field in field_names
        }

    def _serialize_object(self, item: object) -> JSONObject:
        result: JSONObject = {}
        for key, value in vars(item).items():
            if key.startswith("_"):
                continue
            result[key] = self._serialize_item(value)
        return result

    def _serialize_sequence(self, items: Sequence[object]) -> list[JSONValue]:
        return [self._serialize_item(value) for value in items]

    def _item_to_csv_row(self, item: object, field_names: list[str]) -> dict[str, str]:
        serialized_raw = self._serialize_item(item)
        if isinstance(serialized_raw, dict):
            serialized: JSONObject = serialized_raw
        else:
            serialized = {"value": serialized_raw}
        row: dict[str, str] = {}

        for field in field_names:
            value = serialized.get(field, "")
            # Handle nested fields with dot notation (e.g., 'identifier.hpo_id')
            if "." in field:
                parts = field.split(".")
                value = self._resolve_nested_value(serialized, parts)
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

    @classmethod
    def _resolve_nested_value(
        cls,
        source: JSONValue,
        path: Sequence[str],
    ) -> JSONValue:
        current: JSONValue = source
        for part in path:
            if isinstance(current, dict):
                current = current.get(part, "")
            elif hasattr(current, part):
                current = cls._coerce_scalar(getattr(current, part, ""))
            else:
                return ""
        return current

    @staticmethod
    def _coerce_scalar(value: object) -> JSONValue:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _get_gene_fields(self) -> list[str]:
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

    def _get_variant_fields(self) -> list[str]:
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

    def _get_phenotype_fields(self) -> list[str]:
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

    def _get_evidence_fields(self) -> list[str]:
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

    @staticmethod
    def _copy_filters(filters: QueryFilters | None) -> QueryFilters:
        return clone_query_filters(filters) or {}

    def get_export_info(self, entity_type: str) -> JSONObject:
        # This would query the repositories for actual counts
        # For now, return static information
        return {
            "entity_type": entity_type,
            "supported_formats": [fmt.value for fmt in ExportFormat],
            "supported_compression": [comp.value for comp in CompressionFormat],
            "estimated_record_count": 0,  # Would be populated from repository
            "last_updated": None,  # Would track when data was last updated
        }


__all__ = ["BulkExportService", "CompressionFormat", "ExportFormat"]
