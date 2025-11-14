"""
Stage executors encapsulating the responsibilities of the ETL pipeline.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

from ..mappers.cross_reference_mapper import CrossReferenceMapper
from ..mappers.gene_variant_mapper import GeneVariantMapper
from ..mappers.variant_phenotype_mapper import VariantPhenotypeMapper
from .stage_models import (
    ExportReport,
    MappedDataBundle,
    NormalizedDataBundle,
    ParsedDataBundle,
    TransformationResult,
    TransformationStage,
    TransformationStatus,
    ValidationSummary,
)

if TYPE_CHECKING:
    from src.type_definitions.common import RawRecord

    from ..normalizers.gene_normalizer import GeneNormalizer, NormalizedGene
    from ..normalizers.phenotype_normalizer import PhenotypeNormalizer
    from ..normalizers.publication_normalizer import PublicationNormalizer
    from ..normalizers.variant_normalizer import VariantNormalizer

ParsedRecord = TypeVar("ParsedRecord")
NormalizedEntityT = TypeVar("NormalizedEntityT")


class BatchParser(Protocol[ParsedRecord]):
    """Protocol describing the parser interface used by the transformer."""

    def parse_batch(self, raw_data: list[RawRecord]) -> list[ParsedRecord]:
        ...

    def validate_parsed_data(self, record: ParsedRecord) -> list[str]:
        ...


@dataclass
class ParsingStageRunner:
    """Execute parsing across all configured sources."""

    parsers: dict[str, BatchParser[object]]

    async def run(
        self,
        raw_data: dict[str, list[RawRecord]],
    ) -> tuple[ParsedDataBundle, TransformationResult]:
        start_time = time.time()
        parsed_data = ParsedDataBundle()
        errors: list[str] = []
        processed_records = 0

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
        return parsed_data, result


@dataclass
class NormalizationStageRunner:
    """Normalize parsed records into canonical entities."""

    gene_normalizer: GeneNormalizer
    variant_normalizer: VariantNormalizer
    phenotype_normalizer: PhenotypeNormalizer
    publication_normalizer: PublicationNormalizer

    def run(
        self,
        parsed_data: ParsedDataBundle,
    ) -> tuple[NormalizedDataBundle, TransformationResult]:
        start_time = time.time()
        normalized = NormalizedDataBundle()
        seen_genes: set[str] = set()

        self._normalize_uniprot_genes(parsed_data, normalized, seen_genes)
        self._normalize_clinvar_genes(parsed_data, normalized, seen_genes)
        self._normalize_clinvar_variants(parsed_data, normalized)
        self._normalize_clinvar_phenotypes(parsed_data, normalized)
        self._normalize_hpo_terms(parsed_data, normalized)
        self._normalize_pubmed_publications(parsed_data, normalized)
        self._normalize_uniprot_publications(parsed_data, normalized)

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
        return normalized, result

    def _normalize_uniprot_genes(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
        seen_genes: set[str],
    ) -> None:
        for protein in parsed_data.uniprot:
            for gene in protein.genes:
                record: RawRecord = cast(
                    "RawRecord",
                    {
                        "symbol": gene.name,
                        "name": gene.name,
                        "id": gene.locus,
                        "synonyms": gene.synonyms,
                    },
                )
                normalized_gene = self.gene_normalizer.normalize(
                    record,
                    source="uniprot",
                )
                self._add_gene_if_unique(
                    normalized,
                    seen_genes,
                    normalized_gene,
                    f"Failed to normalize UniProt gene: {gene.name}",
                )

    def _normalize_clinvar_genes(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
        seen_genes: set[str],
    ) -> None:
        for variant in parsed_data.clinvar:
            gene_record: RawRecord = cast(
                "RawRecord",
                {
                    "gene_symbol": variant.gene_symbol,
                    "gene_id": variant.gene_id,
                    "gene_name": variant.gene_name,
                },
            )
            normalized_gene = self.gene_normalizer.normalize(
                gene_record,
                source="clinvar",
            )
            error_message = (
                f"Failed to normalize ClinVar gene: {variant.gene_symbol}"
                if variant.gene_symbol
                else None
            )
            self._add_gene_if_unique(
                normalized,
                seen_genes,
                normalized_gene,
                error_message,
            )

    def _normalize_clinvar_variants(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
    ) -> None:
        for variant in parsed_data.clinvar:
            variant_record: RawRecord = cast(
                "RawRecord",
                {
                    "clinvar_id": variant.clinvar_id,
                    "variant_id": variant.variant_id,
                    "variation_name": variant.variation_name,
                    "gene_symbol": variant.gene_symbol,
                    "chromosome": variant.chromosome,
                    "start_position": variant.start_position,
                    "reference_allele": variant.reference_allele,
                    "alternate_allele": variant.alternate_allele,
                    "clinical_significance": variant.clinical_significance.value,
                },
            )
            normalized_variant = self.variant_normalizer.normalize(
                variant_record,
                source="clinvar",
            )
            self._append_entity_or_error(
                normalized.variants,
                normalized_variant,
                normalized.errors,
                f"Failed to normalize ClinVar variant: {variant.clinvar_id}",
            )

    def _normalize_clinvar_phenotypes(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
    ) -> None:
        for variant in parsed_data.clinvar:
            for phenotype_name in variant.phenotypes:
                phenotype_record: RawRecord = cast(
                    "RawRecord",
                    {"name": phenotype_name},
                )
                normalized_phenotype = self.phenotype_normalizer.normalize(
                    phenotype_record,
                    source="clinvar",
                )
                self._append_entity_or_error(
                    normalized.phenotypes,
                    normalized_phenotype,
                    normalized.errors,
                    f"Failed to normalize ClinVar phenotype: {phenotype_name}",
                )

    def _normalize_hpo_terms(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
    ) -> None:
        for term in parsed_data.hpo:
            hpo_record: RawRecord = {
                "hpo_id": term.hpo_id,
                "name": term.name,
                "definition": term.definition,
                "synonyms": term.synonyms,
            }
            normalized_phenotype = self.phenotype_normalizer.normalize(
                hpo_record,
                source="hpo",
            )
            self._append_entity_or_error(
                normalized.phenotypes,
                normalized_phenotype,
                normalized.errors,
                f"Failed to normalize HPO term: {term.hpo_id}",
            )

    def _normalize_pubmed_publications(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
    ) -> None:
        for publication in parsed_data.pubmed:
            authors = [
                f"{author.last_name}, {author.first_name}".strip(", ")
                for author in publication.authors
                if author.last_name
            ]
            publication_date = (
                publication.publication_date.isoformat()
                if publication.publication_date
                else None
            )
            pub_record: RawRecord = {
                "pubmed_id": publication.pubmed_id,
                "title": publication.title,
                "authors": authors,
                "journal": (publication.journal.title if publication.journal else None),
                "publication_date": publication_date,
                "doi": publication.doi,
                "pmc_id": publication.pmc_id,
            }
            normalized_publication = self.publication_normalizer.normalize(
                pub_record,
                source="pubmed",
            )
            self._append_entity_or_error(
                normalized.publications,
                normalized_publication,
                normalized.errors,
                f"Failed to normalize PubMed publication: {publication.pubmed_id}",
            )

    def _normalize_uniprot_publications(
        self,
        parsed_data: ParsedDataBundle,
        normalized: NormalizedDataBundle,
    ) -> None:
        for protein in parsed_data.uniprot:
            for reference in protein.references:
                normalized_publication = self.publication_normalizer.normalize(
                    cast("RawRecord", {"citation": asdict(reference)}),
                    source="uniprot",
                )
                if normalized_publication:
                    normalized.publications.append(normalized_publication)

    def _append_entity_or_error(
        self,
        collection: list[NormalizedEntityT],
        entity: NormalizedEntityT | None,
        errors: list[str],
        error_message: str,
    ) -> None:
        if entity is not None:
            collection.append(entity)
        else:
            errors.append(error_message)

    def _add_gene_if_unique(
        self,
        normalized: NormalizedDataBundle,
        seen_genes: set[str],
        normalized_gene: NormalizedGene | None,
        error_message: str | None,
    ) -> None:
        if normalized_gene:
            primary_id = getattr(normalized_gene, "primary_id", None)
            if primary_id and primary_id not in seen_genes:
                normalized.genes.append(normalized_gene)
                seen_genes.add(primary_id)
        elif error_message:
            normalized.errors.append(error_message)


@dataclass
class MappingStageRunner:
    """Create cross-references between normalized entities."""

    def run(
        self,
        normalized_data: NormalizedDataBundle,
    ) -> tuple[MappedDataBundle, TransformationResult]:
        start_time = time.time()
        gene_mapper = GeneVariantMapper()
        variant_mapper = VariantPhenotypeMapper()
        cross_mapper = CrossReferenceMapper()
        mapped = MappedDataBundle(
            gene_variant_mapper=gene_mapper,
            variant_phenotype_mapper=variant_mapper,
        )
        errors: list[str] = []

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
                        variant,
                        phenotype,
                    )
                    if phenotype_link:
                        mapped.variant_phenotype_links.append(phenotype_link)
                        cross_mapper.add_reference(
                            variant.primary_id,
                            phenotype.primary_id,
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
        return mapped, result


@dataclass
class ValidationStageRunner:
    """Validate mapped relationships to ensure structural quality."""

    def run(
        self,
        mapped_data: MappedDataBundle,
    ) -> tuple[ValidationSummary, TransformationResult]:
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
        return summary, result


@dataclass
class ExportStageRunner:
    """Export normalized entities and mapping summaries to disk."""

    output_dir: Path

    def run(
        self,
        normalized_data: NormalizedDataBundle,
        mapped_data: MappedDataBundle,
    ) -> tuple[ExportReport, TransformationResult]:
        start_time = time.time()
        report = ExportReport()

        try:
            for entity_type, entities in normalized_data.as_dict().items():
                if not isinstance(entities, list) or not entities:
                    continue
                filename = f"{entity_type}_normalized.json"
                filepath = self.output_dir / filename
                serializable_entities = [
                    {
                        "primary_id": entity.primary_id,
                        "display_name": getattr(
                            entity,
                            "name",
                            getattr(entity, "symbol", None),
                        ),
                        "source": getattr(entity, "source", "unknown"),
                        "confidence_score": getattr(entity, "confidence_score", None),
                    }
                    for entity in entities
                ]
                with filepath.open("w", encoding="utf-8") as handle:
                    json.dump(serializable_entities, handle, indent=2, default=str)
                report.files_created.append(str(filepath))

            mapping_summary = {
                "gene_variant_count": len(mapped_data.gene_variant_links),
                "variant_phenotype_count": len(mapped_data.variant_phenotype_links),
                "networks_count": len(mapped_data.networks),
            }
            mappings_file = self.output_dir / "entity_mappings.json"
            with mappings_file.open("w", encoding="utf-8") as handle:
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
        return report, result


__all__ = [
    "BatchParser",
    "ExportStageRunner",
    "MappingStageRunner",
    "NormalizationStageRunner",
    "ParsingStageRunner",
    "ValidationStageRunner",
]
