"""
ETL Transformation orchestrator.

Coordinates the Extract-Transform-Load pipeline by applying parsers,
normalizers, and relationship mappers in a strictly typed workflow.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, TypeVar, cast

from ..mappers.cross_reference_mapper import CrossReferenceMapper
from ..mappers.gene_variant_mapper import GeneVariantLink, GeneVariantMapper
from ..mappers.variant_phenotype_mapper import (
    VariantPhenotypeLink,
    VariantPhenotypeMapper,
)
from ..normalizers.gene_normalizer import GeneNormalizer, NormalizedGene
from ..normalizers.phenotype_normalizer import (
    NormalizedPhenotype,
    PhenotypeNormalizer,
)
from ..normalizers.publication_normalizer import (
    NormalizedPublication,
    PublicationNormalizer,
)
from ..normalizers.variant_normalizer import NormalizedVariant, VariantNormalizer
from ..parsers.clinvar_parser import ClinVarParser, ClinVarVariant
from ..parsers.hpo_parser import HPOParser, HPOTerm
from ..parsers.pubmed_parser import PubMedParser, PubMedPublication
from ..parsers.uniprot_parser import UniProtParser, UniProtProtein

RawRecord = Dict[str, Any]
ParsedRecord = TypeVar("ParsedRecord")
NormalizedRecord = TypeVar("NormalizedRecord", covariant=True)


class BatchParser(Protocol[ParsedRecord]):
    """Protocol describing the parser interface used by the transformer."""

    def parse_batch(self, raw_data: List[RawRecord]) -> List[ParsedRecord]:
        ...

    def validate_parsed_data(self, record: ParsedRecord) -> List[str]:
        ...


class EntityNormalizer(Protocol[NormalizedRecord]):
    """Protocol describing the normalizer interface used by the transformer."""

    def normalize(
        self, raw_entity: RawRecord, source: str = "unknown"
    ) -> Optional[NormalizedRecord]:
        ...


@dataclass
class ParsedDataBundle:
    """Container for parsed source records."""

    clinvar: List[ClinVarVariant] = field(default_factory=list)
    pubmed: List[PubMedPublication] = field(default_factory=list)
    hpo: List[HPOTerm] = field(default_factory=list)
    uniprot: List[UniProtProtein] = field(default_factory=list)
    extras: Dict[str, List[Any]] = field(default_factory=dict)

    def add(self, source: str, records: List[Any]) -> None:
        """Persist parsed records under the appropriate collection."""
        if source == "clinvar":
            self.clinvar = cast(List[ClinVarVariant], records)
        elif source == "pubmed":
            self.pubmed = cast(List[PubMedPublication], records)
        elif source == "hpo":
            self.hpo = cast(List[HPOTerm], records)
        elif source == "uniprot":
            self.uniprot = cast(List[UniProtProtein], records)
        else:
            self.extras[source] = records

    def total_records(self) -> int:
        """Count the total number of parsed records."""
        return (
            len(self.clinvar)
            + len(self.pubmed)
            + len(self.hpo)
            + len(self.uniprot)
            + sum(len(values) for values in self.extras.values())
        )

    def as_dict(self) -> Dict[str, List[Any]]:
        """Expose parsed data as plain dictionaries for reporting."""
        payload: Dict[str, List[Any]] = {
            "clinvar": list(self.clinvar),
            "pubmed": list(self.pubmed),
            "hpo": list(self.hpo),
            "uniprot": list(self.uniprot),
        }
        payload.update({key: list(values) for key, values in self.extras.items()})
        return payload


@dataclass
class NormalizedDataBundle:
    """Container for normalized entities."""

    genes: List[NormalizedGene] = field(default_factory=list)
    variants: List[NormalizedVariant] = field(default_factory=list)
    phenotypes: List[NormalizedPhenotype] = field(default_factory=list)
    publications: List[NormalizedPublication] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def total_records(self) -> int:
        return (
            len(self.genes)
            + len(self.variants)
            + len(self.phenotypes)
            + len(self.publications)
        )

    def as_dict(self) -> Dict[str, List[Any]]:
        return {
            "genes": list(self.genes),
            "variants": list(self.variants),
            "phenotypes": list(self.phenotypes),
            "publications": list(self.publications),
        }


@dataclass
class MappedDataBundle:
    """Container for relationship mapping outputs."""

    gene_variant_links: List[GeneVariantLink] = field(default_factory=list)
    variant_phenotype_links: List[VariantPhenotypeLink] = field(default_factory=list)
    networks: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    gene_variant_mapper: GeneVariantMapper | None = None
    variant_phenotype_mapper: VariantPhenotypeMapper | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "gene_variant_links": [asdict(link) for link in self.gene_variant_links],
            "variant_phenotype_links": [
                asdict(link) for link in self.variant_phenotype_links
            ],
            "networks": self.networks,
        }

    def relationship_count(self) -> int:
        return len(self.gene_variant_links) + len(self.variant_phenotype_links)


@dataclass
class ValidationSummary:
    """Summary of validation outcomes."""

    passed: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)

    def record_success(self) -> None:
        self.passed += 1

    def record_failure(self, messages: Sequence[str]) -> None:
        self.failed += 1
        self.errors.extend(messages)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "errors": list(self.errors),
        }


@dataclass
class ExportReport:
    """Details of export artefacts."""

    files_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "files_created": list(self.files_created),
            "errors": list(self.errors),
        }


class TransformationStage(Enum):
    """Stages of the ETL transformation pipeline."""

    PARSING = "parsing"
    NORMALIZATION = "normalization"
    MAPPING = "mapping"
    VALIDATION = "validation"
    EXPORT = "export"


class TransformationStatus(Enum):
    """Status of transformation operations."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class TransformationResult:
    """Result of a transformation operation."""

    stage: TransformationStage
    status: TransformationStatus
    records_processed: int
    records_failed: int
    data: Dict[str, Any]
    errors: List[str]
    duration_seconds: float
    timestamp: float


@dataclass
class ETLTransformationMetrics:
    """Metrics collected during ETL transformation."""

    total_input_records: int
    parsed_records: int
    normalized_records: int
    mapped_relationships: int
    validation_errors: int
    processing_time_seconds: float
    stage_metrics: Dict[str, Dict[str, Any]]


class ETLTransformer:
    """
    Orchestrates the complete ETL transformation pipeline.

    Applies parsers, normalizers, and mappers in sequence to transform
    raw biomedical data into standardized, cross-referenced datasets.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("data/transformed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.parsers: Dict[str, BatchParser[Any]] = {
            "clinvar": ClinVarParser(),
            "pubmed": PubMedParser(),
            "hpo": HPOParser(),
            "uniprot": UniProtParser(),
        }

        self.gene_normalizer = GeneNormalizer()
        self.variant_normalizer = VariantNormalizer()
        self.phenotype_normalizer = PhenotypeNormalizer()
        self.publication_normalizer = PublicationNormalizer()

        self.results: Dict[str, TransformationResult] = {}
        self.metrics = ETLTransformationMetrics(
            total_input_records=0,
            parsed_records=0,
            normalized_records=0,
            mapped_relationships=0,
            validation_errors=0,
            processing_time_seconds=0.0,
            stage_metrics={},
        )

    async def transform_all_sources(
        self, raw_data: Dict[str, List[RawRecord]], validate: bool = True
    ) -> Dict[str, Any]:
        """
        Transform data from all sources through the complete ETL pipeline.

        Args:
            raw_data: Dictionary mapping source names to lists of raw data records.
            validate: Whether to perform validation during transformation.

        Returns:
            Dictionary with transformed data, metadata, and metrics.
        """
        start_time = time.time()
        results: Dict[str, Any] = {}
        all_errors: List[str] = []

        parsed_data = await self._parse_all_sources(raw_data)
        results["parsed"] = self._stage_to_dict(parsed_data)

        normalized_data = self._normalize_all_entities(parsed_data)
        results["normalized"] = self._stage_to_dict(normalized_data)
        all_errors.extend(self._stage_errors(normalized_data))

        mapped_data = self._create_cross_references(normalized_data)
        results["mapped"] = self._stage_to_dict(mapped_data)

        validation_summary: Optional[ValidationSummary] = None
        if validate:
            validation_summary = self._validate_transformed_data(mapped_data)
            results["validation"] = self._stage_to_dict(validation_summary)
            all_errors.extend(self._stage_errors(validation_summary))

        export_report = self._export_transformed_data(normalized_data, mapped_data)
        results["export"] = self._stage_to_dict(export_report)
        all_errors.extend(self._stage_errors(export_report))

        total_time = time.time() - start_time
        self._update_metrics(
            parsed_data, normalized_data, mapped_data, validation_summary, total_time
        )

        results["metadata"] = {
            "processing_time_seconds": total_time,
            "total_errors": len(all_errors),
            "errors": all_errors,
            "metrics": self._get_metrics_summary(),
        }

        return results

    async def _parse_all_sources(
        self, raw_data: Dict[str, List[RawRecord]]
    ) -> ParsedDataBundle:
        """Parse data from all configured sources."""
        start_time = time.time()
        parsed_data = ParsedDataBundle()
        errors: List[str] = []
        processed_records = 0

        self.metrics.total_input_records = sum(
            len(records) for records in raw_data.values()
        )

        for source_name, source_records in raw_data.items():
            parser = self.parsers.get(source_name)
            if parser is None:
                errors.append(f"No parser available for source: {source_name}")
                continue

            try:
                parsed_records = parser.parse_batch(source_records)
                parsed_data.add(source_name, parsed_records)
                processed_records += len(parsed_records)

                for record in parsed_records:
                    validation_errors = parser.validate_parsed_data(record)
                    if validation_errors:
                        errors.extend(validation_errors)
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"Failed to parse {source_name}: {exc}")

        result = TransformationResult(
            stage=TransformationStage.PARSING,
            status=(
                TransformationStatus.COMPLETED
                if not errors
                else TransformationStatus.PARTIAL
            ),
            records_processed=processed_records,
            records_failed=len(errors),
            data=parsed_data.as_dict(),
            errors=errors,
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["parsing"] = result
        return parsed_data

    @staticmethod
    def _stage_to_dict(stage_result: Any) -> Dict[str, Any]:
        if hasattr(stage_result, "as_dict"):
            return cast(Dict[str, Any], stage_result.as_dict())
        if isinstance(stage_result, dict):
            return stage_result
        if hasattr(stage_result, "__dict__"):
            return dict(cast(Dict[str, Any], stage_result.__dict__))
        return {}

    @staticmethod
    def _stage_errors(stage_result: Any) -> List[str]:
        if hasattr(stage_result, "errors"):
            errors = getattr(stage_result, "errors")
            if isinstance(errors, list):
                return errors
        if isinstance(stage_result, dict):
            errors = stage_result.get("errors", [])
            if isinstance(errors, list):
                return errors
        return []

    @staticmethod
    def _safe_total_records(stage: Any) -> int:
        if hasattr(stage, "total_records"):
            try:
                return int(stage.total_records())
            except Exception:
                return 0
        if isinstance(stage, dict):
            return sum(len(v) for v in stage.values() if isinstance(v, list))
        return 0

    @staticmethod
    def _safe_relationship_count(stage: Any) -> int:
        if hasattr(stage, "relationship_count"):
            try:
                return int(stage.relationship_count())
            except Exception:
                return 0
        if isinstance(stage, dict):
            return sum(len(v) for v in stage.values() if isinstance(v, list))
        return 0

    @staticmethod
    def _safe_validation_failures(validation: Optional[Any]) -> int:
        if validation is None:
            return 0
        if hasattr(validation, "failed"):
            try:
                return int(validation.failed)
            except Exception:
                return 0
        if isinstance(validation, dict):
            failed = validation.get("failed", 0)
            try:
                return int(failed)
            except Exception:
                return 0
        return 0

    def _normalize_all_entities(
        self, parsed_data: ParsedDataBundle
    ) -> NormalizedDataBundle:
        """Normalize parsed entities into canonical structures."""
        start_time = time.time()
        normalized = NormalizedDataBundle()

        # Normalize gene records
        seen_genes: set[str] = set()
        for protein in parsed_data.uniprot:
            for gene in protein.genes:
                record = {
                    "symbol": gene.name,
                    "name": gene.name,
                    "id": gene.locus,
                    "synonyms": gene.synonyms,
                }
                normalized_gene = self.gene_normalizer.normalize(
                    record, source="uniprot"
                )
                if normalized_gene:
                    if normalized_gene.primary_id not in seen_genes:
                        normalized.genes.append(normalized_gene)
                        seen_genes.add(normalized_gene.primary_id)
                else:
                    normalized.errors.append(
                        f"Failed to normalize UniProt gene: {gene.name}"
                    )

        for variant in parsed_data.clinvar:
            gene_record = {
                "gene_symbol": variant.gene_symbol,
                "gene_id": variant.gene_id,
                "gene_name": variant.gene_name,
            }
            normalized_gene = self.gene_normalizer.normalize(
                gene_record, source="clinvar"
            )
            if normalized_gene:
                if normalized_gene.primary_id not in seen_genes:
                    normalized.genes.append(normalized_gene)
                    seen_genes.add(normalized_gene.primary_id)
            elif variant.gene_symbol:
                normalized.errors.append(
                    f"Failed to normalize ClinVar gene: {variant.gene_symbol}"
                )

        # Normalize variants
        for variant in parsed_data.clinvar:
            variant_record = {
                "clinvar_id": variant.clinvar_id,
                "variant_id": variant.variant_id,
                "variation_name": variant.variation_name,
                "gene_symbol": variant.gene_symbol,
                "chromosome": variant.chromosome,
                "start_position": variant.start_position,
                "reference_allele": variant.reference_allele,
                "alternate_allele": variant.alternate_allele,
                "clinical_significance": variant.clinical_significance.value,
            }
            normalized_variant = self.variant_normalizer.normalize(
                variant_record, source="clinvar"
            )
            if normalized_variant:
                normalized.variants.append(normalized_variant)
            else:
                normalized.errors.append(
                    f"Failed to normalize ClinVar variant: {variant.clinvar_id}"
                )

        # Normalize phenotypes
        for variant in parsed_data.clinvar:
            for phenotype_name in variant.phenotypes:
                phenotype_record = {"name": phenotype_name}
                normalized_phenotype = self.phenotype_normalizer.normalize(
                    phenotype_record, source="clinvar"
                )
                if normalized_phenotype:
                    normalized.phenotypes.append(normalized_phenotype)
                else:
                    normalized.errors.append(
                        f"Failed to normalize ClinVar phenotype: {phenotype_name}"
                    )

        for term in parsed_data.hpo:
            hpo_record: Dict[str, Any] = {
                "hpo_id": term.hpo_id,
                "name": term.name,
                "definition": term.definition,
                "synonyms": term.synonyms,
            }
            normalized_phenotype = self.phenotype_normalizer.normalize(
                hpo_record, source="hpo"
            )
            if normalized_phenotype:
                normalized.phenotypes.append(normalized_phenotype)
            else:
                normalized.errors.append(f"Failed to normalize HPO term: {term.hpo_id}")

        # Normalize publications
        for publication in parsed_data.pubmed:
            authors = [
                f"{author.last_name}, {author.first_name}".strip(", ")
                for author in publication.authors
                if author.last_name
            ]
            pub_record: Dict[str, Any] = {
                "pubmed_id": publication.pubmed_id,
                "title": publication.title,
                "authors": authors,
                "journal": (publication.journal.title if publication.journal else None),
                "publication_date": publication.publication_date,
                "doi": publication.doi,
                "pmc_id": publication.pmc_id,
            }
            normalized_publication = self.publication_normalizer.normalize(
                pub_record, source="pubmed"
            )
            if normalized_publication:
                normalized.publications.append(normalized_publication)
            else:
                normalized.errors.append(
                    f"Failed to normalize PubMed publication: {publication.pubmed_id}"
                )

        for protein in parsed_data.uniprot:
            for reference in protein.references:
                normalized_publication = self.publication_normalizer.normalize(
                    {"citation": asdict(reference)}, source="uniprot"
                )
                if normalized_publication:
                    normalized.publications.append(normalized_publication)

        result = TransformationResult(
            stage=TransformationStage.NORMALIZATION,
            status=(
                TransformationStatus.COMPLETED
                if not normalized.errors
                else TransformationStatus.PARTIAL
            ),
            records_processed=normalized.total_records(),
            records_failed=len(normalized.errors),
            data=normalized.as_dict(),
            errors=normalized.errors,
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["normalization"] = result
        return normalized

    def _create_cross_references(
        self, normalized_data: NormalizedDataBundle
    ) -> MappedDataBundle:
        """Create cross-references between normalized entities."""
        start_time = time.time()
        gene_mapper = GeneVariantMapper()
        variant_mapper = VariantPhenotypeMapper()
        cross_mapper = CrossReferenceMapper()
        mapped = MappedDataBundle(
            gene_variant_mapper=gene_mapper, variant_phenotype_mapper=variant_mapper
        )
        errors: List[str] = []

        try:
            gene_lookup = {
                gene.primary_id.lower(): gene for gene in normalized_data.genes
            }
            for gene in normalized_data.genes:
                if gene.symbol:
                    gene_lookup[gene.symbol.lower()] = gene

            for variant in normalized_data.variants:
                variant_gene_symbol = (
                    variant.gene_symbol.lower() if variant.gene_symbol else None
                )
                if variant_gene_symbol and variant_gene_symbol in gene_lookup:
                    gene = gene_lookup[variant_gene_symbol]
                    location = variant.genomic_location
                    if (
                        location is not None
                        and location.position is not None
                        and location.chromosome
                    ):
                        gene_mapper.add_gene_coordinates(
                            gene.primary_id,
                            location.chromosome,
                            location.position,
                            location.position,
                        )
                    gene_link = gene_mapper.map_gene_variant_relationship(gene, variant)
                    if gene_link:
                        mapped.gene_variant_links.append(gene_link)
                        cross_mapper.add_reference(gene.primary_id, variant.primary_id)

            for variant in normalized_data.variants:
                for phenotype in normalized_data.phenotypes:
                    phenotype_link = variant_mapper.map_variant_phenotype_relationship(
                        variant, phenotype
                    )
                    if phenotype_link:
                        mapped.variant_phenotype_links.append(phenotype_link)
                        cross_mapper.add_reference(
                            variant.primary_id, phenotype.primary_id
                        )

            for gene in normalized_data.genes:
                network = cross_mapper.build_cross_reference_network(gene.primary_id)
                if network:
                    mapped.networks[gene.primary_id] = network

        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"Cross-reference mapping failed: {exc}")

        result = TransformationResult(
            stage=TransformationStage.MAPPING,
            status=(
                TransformationStatus.COMPLETED
                if not errors
                else TransformationStatus.PARTIAL
            ),
            records_processed=mapped.relationship_count(),
            records_failed=len(errors),
            data=mapped.as_dict(),
            errors=errors,
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["mapping"] = result
        return mapped

    def _validate_transformed_data(
        self, mapped_data: MappedDataBundle
    ) -> ValidationSummary:
        """Validate mapped relationships to ensure structural quality."""
        start_time = time.time()
        summary = ValidationSummary()

        gene_mapper = mapped_data.gene_variant_mapper
        if gene_mapper:
            for gene_link in mapped_data.gene_variant_links:
                issues = gene_mapper.validate_mapping(gene_link)
                if issues:
                    summary.record_failure(issues)
                else:
                    summary.record_success()

        variant_mapper = mapped_data.variant_phenotype_mapper
        if variant_mapper:
            for variant_link in mapped_data.variant_phenotype_links:
                issues = variant_mapper.validate_mapping(variant_link)
                if issues:
                    summary.record_failure(issues)
                else:
                    summary.record_success()

        result = TransformationResult(
            stage=TransformationStage.VALIDATION,
            status=(
                TransformationStatus.COMPLETED
                if summary.failed == 0
                else TransformationStatus.PARTIAL
            ),
            records_processed=summary.passed + summary.failed,
            records_failed=summary.failed,
            data=summary.as_dict(),
            errors=list(summary.errors),
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["validation"] = result
        return summary

    def _export_transformed_data(
        self,
        normalized_data: NormalizedDataBundle,
        mapped_data: MappedDataBundle,
    ) -> ExportReport:
        """Export normalized entities and mapping summaries to disk."""
        start_time = time.time()
        report = ExportReport()

        try:
            for entity_type, entities in normalized_data.as_dict().items():
                if not entities:
                    continue
                filename = f"{entity_type}_normalized.json"
                filepath = self.output_dir / filename
                serializable_entities = [
                    {
                        "primary_id": entity.primary_id,
                        "display_name": getattr(
                            entity, "name", getattr(entity, "symbol", None)
                        ),
                        "source": getattr(entity, "source", "unknown"),
                        "confidence_score": getattr(entity, "confidence_score", None),
                    }
                    for entity in entities
                ]
                with open(filepath, "w", encoding="utf-8") as handle:
                    json.dump(serializable_entities, handle, indent=2, default=str)
                report.files_created.append(str(filepath))

            mapping_summary = {
                "gene_variant_count": len(mapped_data.gene_variant_links),
                "variant_phenotype_count": len(mapped_data.variant_phenotype_links),
                "networks_count": len(mapped_data.networks),
            }
            mappings_file = self.output_dir / "entity_mappings.json"
            with open(mappings_file, "w", encoding="utf-8") as handle:
                json.dump(mapping_summary, handle, indent=2)
            report.files_created.append(str(mappings_file))

        except Exception as exc:  # pragma: no cover - defensive
            report.errors.append(f"Export failed: {exc}")

        result = TransformationResult(
            stage=TransformationStage.EXPORT,
            status=(
                TransformationStatus.COMPLETED
                if not report.errors
                else TransformationStatus.FAILED
            ),
            records_processed=len(report.files_created),
            records_failed=len(report.errors),
            data=report.as_dict(),
            errors=list(report.errors),
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["export"] = result
        return report

    def _update_metrics(
        self,
        parsed: ParsedDataBundle,
        normalized: NormalizedDataBundle,
        mapped: MappedDataBundle,
        validation: Optional[ValidationSummary],
        total_time: float,
    ) -> None:
        """Update aggregate transformation metrics."""
        self.metrics.processing_time_seconds = total_time
        self.metrics.parsed_records = self._safe_total_records(parsed)
        self.metrics.normalized_records = self._safe_total_records(normalized)
        self.metrics.mapped_relationships = self._safe_relationship_count(mapped)
        self.metrics.validation_errors = self._safe_validation_failures(validation)
        self.metrics.stage_metrics = {
            stage: result.__dict__ for stage, result in self.results.items()
        }

    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of transformation metrics."""
        return {
            "total_input_records": self.metrics.total_input_records,
            "parsed_records": self.metrics.parsed_records,
            "normalized_records": self.metrics.normalized_records,
            "mapped_relationships": self.metrics.mapped_relationships,
            "validation_errors": self.metrics.validation_errors,
            "processing_time_seconds": self.metrics.processing_time_seconds,
            "stage_durations": {
                stage: result.duration_seconds for stage, result in self.results.items()
            },
        }

    def get_transformation_status(self) -> Dict[str, Any]:
        """
        Get the current status of the transformation pipeline.

        Returns:
            Dictionary with stage status and metrics summary.
        """
        return {
            "stages": {k: v.status.value for k, v in self.results.items()},
            "metrics": self._get_metrics_summary(),
            "last_updated": max(
                (result.timestamp for result in self.results.values()), default=None
            ),
        }


__all__ = [
    "ETLTransformer",
    "TransformationStage",
    "TransformationStatus",
    "TransformationResult",
    "ETLTransformationMetrics",
]
