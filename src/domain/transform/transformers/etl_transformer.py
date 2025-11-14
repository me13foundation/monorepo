"""
ETL Transformation orchestrator.

Coordinates the Extract-Transform-Load pipeline by applying parsers,
normalizers, and relationship mappers in a strictly typed workflow.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import cast

from src.type_definitions.common import RawRecord  # noqa: TC001

from ..normalizers.gene_normalizer import GeneNormalizer
from ..normalizers.phenotype_normalizer import PhenotypeNormalizer
from ..normalizers.publication_normalizer import PublicationNormalizer
from ..normalizers.variant_normalizer import VariantNormalizer
from ..parsers.clinvar_parser import ClinVarParser
from ..parsers.hpo_parser import HPOParser
from ..parsers.pubmed_parser import PubMedParser
from ..parsers.uniprot_parser import UniProtParser
from .metrics_tracker import StageArtifacts, TransformationMetricsTracker
from .stage_handlers import (
    BatchParser,
    ExportStageRunner,
    MappingStageRunner,
    NormalizationStageRunner,
    ParsingStageRunner,
    ValidationStageRunner,
)
from .stage_models import (
    ETLTransformationMetrics,
    ExportReport,
    MappedDataBundle,
    NormalizedDataBundle,
    ParsedDataBundle,
    StageData,
    TransformationResult,
    TransformationStage,
    TransformationStatus,
    ValidationSummary,
)
from .stage_utils import stage_errors, stage_to_dict


class ETLTransformer:
    """
    Orchestrates the complete ETL transformation pipeline.

    Applies parsers, normalizers, and mappers in sequence to transform
    raw biomedical data into standardized, cross-referenced datasets.
    """

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("data/transformed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.parsers: dict[str, BatchParser[object]] = {
            "clinvar": cast("BatchParser[object]", ClinVarParser()),
            "pubmed": cast("BatchParser[object]", PubMedParser()),
            "hpo": cast("BatchParser[object]", HPOParser()),
            "uniprot": cast("BatchParser[object]", UniProtParser()),
        }

        self.gene_normalizer = GeneNormalizer()
        self.variant_normalizer = VariantNormalizer()
        self.phenotype_normalizer = PhenotypeNormalizer()
        self.publication_normalizer = PublicationNormalizer()

        self._parsing_stage = ParsingStageRunner(self.parsers)
        self._normalization_stage = NormalizationStageRunner(
            self.gene_normalizer,
            self.variant_normalizer,
            self.phenotype_normalizer,
            self.publication_normalizer,
        )
        self._mapping_stage = MappingStageRunner()
        self._validation_stage = ValidationStageRunner()
        self._export_stage = ExportStageRunner(self.output_dir)

        self.results: dict[str, TransformationResult] = {}
        self.metrics_tracker = TransformationMetricsTracker()
        # Backwards-compatible reference to metrics dataclass
        self.metrics: ETLTransformationMetrics = self.metrics_tracker.metrics

    async def transform_all_sources(
        self,
        raw_data: dict[str, list[RawRecord]],
        validate: bool = True,
    ) -> StageData:
        """
        Transform data from all sources through the complete ETL pipeline.

        Args:
            raw_data: Dictionary mapping source names to lists of raw data records.
            validate: Whether to perform validation during transformation.

        Returns:
            Dictionary with transformed data, metadata, and metrics.
        """
        start_time = time.time()
        self.results = {}
        results: dict[str, object] = {}
        all_errors: list[str] = []

        total_input_records = sum(len(records) for records in raw_data.values())
        self.metrics_tracker.set_total_input_records(total_input_records)

        parsed_data = await self._parse_all_sources(raw_data)
        results["parsed"] = stage_to_dict(parsed_data)

        normalized_data = self._normalize_all_entities(parsed_data)
        results["normalized"] = stage_to_dict(normalized_data)
        all_errors.extend(stage_errors(normalized_data))

        mapped_data = self._create_cross_references(normalized_data)
        results["mapped"] = stage_to_dict(mapped_data)

        validation_summary: ValidationSummary | None = None
        if validate:
            validation_summary = self._validate_transformed_data(mapped_data)
            results["validation"] = stage_to_dict(validation_summary)
            all_errors.extend(stage_errors(validation_summary))

        export_report = self._export_transformed_data(normalized_data, mapped_data)
        results["export"] = stage_to_dict(export_report)
        all_errors.extend(stage_errors(export_report))

        total_time = time.time() - start_time
        self.metrics_tracker.update_metrics(
            artifacts=StageArtifacts(
                parsed=parsed_data,
                normalized=normalized_data,
                mapped=mapped_data,
                validation=validation_summary,
            ),
            total_time=total_time,
            stage_results=self.results,
        )

        results["metadata"] = {
            "processing_time_seconds": total_time,
            "total_errors": len(all_errors),
            "errors": all_errors,
            "metrics": self.metrics_tracker.summary(),
        }

        return results

    def get_transformation_status(self) -> StageData:
        """
        Get the current status of the transformation pipeline.

        Returns:
            Dictionary with stage status and metrics summary.
        """
        last_updated = max(
            (result.timestamp for result in self.results.values()),
            default=None,
        )
        return {
            "stages": {k: v.status.value for k, v in self.results.items()},
            "metrics": self.metrics_tracker.summary(),
            "last_updated": last_updated,
        }

    async def _parse_all_sources(
        self,
        raw_data: dict[str, list[RawRecord]],
    ) -> ParsedDataBundle:
        """Wrapper around the parsing stage for compatibility with existing tests."""
        parsed_data, parsing_result = await self._parsing_stage.run(raw_data)
        self._store_stage_result(TransformationStage.PARSING, parsing_result)
        return parsed_data

    def _normalize_all_entities(
        self,
        parsed_data: ParsedDataBundle,
    ) -> NormalizedDataBundle:
        """Wrapper around the normalization stage for compatibility with existing tests."""
        normalized_data, normalization_result = self._normalization_stage.run(
            parsed_data,
        )
        self._store_stage_result(
            TransformationStage.NORMALIZATION,
            normalization_result,
        )
        return normalized_data

    def _create_cross_references(
        self,
        normalized_data: NormalizedDataBundle,
    ) -> MappedDataBundle:
        """Wrapper around the mapping stage for compatibility with existing tests."""
        mapped_data, mapping_result = self._mapping_stage.run(normalized_data)
        self._store_stage_result(TransformationStage.MAPPING, mapping_result)
        return mapped_data

    def _validate_transformed_data(
        self,
        mapped_data: MappedDataBundle,
    ) -> ValidationSummary:
        """Wrapper around the validation stage for compatibility with existing tests."""
        validation_summary, validation_result = self._validation_stage.run(mapped_data)
        self._store_stage_result(TransformationStage.VALIDATION, validation_result)
        return validation_summary

    def _export_transformed_data(
        self,
        normalized_data: NormalizedDataBundle,
        mapped_data: MappedDataBundle,
    ) -> ExportReport:
        """Wrapper around the export stage for compatibility with existing tests."""
        export_report, export_result = self._export_stage.run(
            normalized_data,
            mapped_data,
        )
        self._store_stage_result(TransformationStage.EXPORT, export_result)
        return export_report

    def _store_stage_result(
        self,
        stage: TransformationStage,
        result: TransformationResult,
    ) -> None:
        """Persist the stage result for later reporting."""
        self.results[stage.value] = result


__all__ = [
    "ETLTransformationMetrics",
    "ETLTransformer",
    "TransformationResult",
    "TransformationStage",
    "TransformationStatus",
]
