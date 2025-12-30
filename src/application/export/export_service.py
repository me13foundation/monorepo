"""
Bulk Export Service for MED13 Resource Library.

Handles large dataset serialization and streaming export capabilities.
"""

import tempfile
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.application.export.export_types import (
    CompressionFormat,
    ExportFormat,
)
from src.application.export.formatters import (
    export_as_csv,
    export_as_json,
    export_as_jsonl,
)
from src.application.export.utils import (
    collect_paginated,
    copy_filters,
    get_evidence_fields,
    get_gene_fields,
    get_phenotype_fields,
    get_variants_fields,
)
from src.application.services import (
    EvidenceApplicationService,
    GeneApplicationService,
    PhenotypeApplicationService,
    VariantApplicationService,
)
from src.type_definitions.common import (
    JSONObject,
    QueryFilters,
)
from src.type_definitions.storage import StorageOperationRecord, StorageUseCase

if TYPE_CHECKING:
    from src.application.services import StorageConfigurationService


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
        storage_service: "StorageConfigurationService | None" = None,
    ):
        self._gene_service = gene_service
        self._variant_service = variant_service
        self._phenotype_service = phenotype_service
        self._evidence_service = evidence_service
        self._storage_service = storage_service

    async def export_to_storage(
        self,
        entity_type: str,
        export_format: ExportFormat,
        user_id: UUID,
        compression: CompressionFormat = CompressionFormat.NONE,
        filters: QueryFilters | None = None,
    ) -> StorageOperationRecord:
        """Export data to a file and store it using the configured EXPORT backend."""
        if not self._storage_service:
            msg = "Storage service not configured for export service"
            raise RuntimeError(msg)

        backend = self._storage_service.resolve_backend_for_use_case(
            StorageUseCase.EXPORT,
        )
        if not backend:
            msg = "No storage backend configured for EXPORT use case"
            raise ValueError(msg)

        suffix = f".{export_format.value}"
        if compression == CompressionFormat.GZIP:
            suffix += ".gz"

        # Create a temporary file to store the export
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
            try:
                for chunk in self.export_data(
                    entity_type,
                    export_format,
                    compression,
                    filters,
                ):
                    if isinstance(chunk, str):
                        tmp.write(chunk.encode("utf-8"))
                    else:
                        tmp.write(chunk)
                tmp_path = Path(tmp.name)
            except Exception:
                Path(tmp.name).unlink(missing_ok=True)
                raise

        try:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            key = f"exports/{entity_type}/{timestamp}_{uuid4().hex[:8]}{suffix}"

            return await self._storage_service.record_store_operation(
                configuration=backend,
                key=key,
                file_path=tmp_path,
                content_type=self._get_content_type(export_format, compression),
                user_id=user_id,
                metadata={
                    "entity_type": entity_type,
                    "format": export_format.value,
                    "compression": compression.value,
                },
            )
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def _get_content_type(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
    ) -> str:
        if compression == CompressionFormat.GZIP:
            return "application/gzip"

        content_types: dict[ExportFormat, str] = {
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv",
            ExportFormat.TSV: "text/tab-separated-values",
            ExportFormat.JSONL: "application/x-jsonlines",
        }
        content_type = content_types.get(export_format)
        if content_type is None:
            msg = f"Unsupported export format: {export_format}"
            raise ValueError(msg)
        return content_type

    def export_data(
        self,
        entity_type: str,
        export_format: ExportFormat,
        compression: CompressionFormat = CompressionFormat.NONE,
        filters: QueryFilters | None = None,
        chunk_size: int = 1000,
    ) -> Generator[str | bytes]:
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
    ) -> Generator[str | bytes]:
        filters_payload = copy_filters(filters)
        search_value = filters_payload.get("search")
        search_term = search_value if isinstance(search_value, str) else None
        genes = collect_paginated(
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
            yield from export_as_json(genes, compression, "genes")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from export_as_csv(
                genes,
                export_format,
                compression,
                get_gene_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from export_as_jsonl(genes, compression)

    def _export_variants(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes]:
        variants = collect_paginated(
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
            yield from export_as_json(variants, compression, "variants")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from export_as_csv(
                variants,
                export_format,
                compression,
                get_variants_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from export_as_jsonl(variants, compression)

    def _export_phenotypes(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes]:
        phenotypes = collect_paginated(
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
            yield from export_as_json(phenotypes, compression, "phenotypes")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from export_as_csv(
                phenotypes,
                export_format,
                compression,
                get_phenotype_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from export_as_jsonl(phenotypes, compression)

    def _export_evidence(
        self,
        export_format: ExportFormat,
        compression: CompressionFormat,
        filters: QueryFilters | None,
        chunk_size: int,
    ) -> Generator[str | bytes]:
        evidence_list = collect_paginated(
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
            yield from export_as_json(evidence_list, compression, "evidence")
        elif export_format in (ExportFormat.CSV, ExportFormat.TSV):
            yield from export_as_csv(
                evidence_list,
                export_format,
                compression,
                get_evidence_fields(),
            )
        elif export_format == ExportFormat.JSONL:
            yield from export_as_jsonl(evidence_list, compression)

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
