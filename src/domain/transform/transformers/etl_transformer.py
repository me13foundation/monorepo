"""
ETL Transformation orchestrator.

Coordinates the complete Extract-Transform-Load transformation pipeline,
applying parsers, normalizers, and mappers in sequence with comprehensive
error handling, metrics collection, and data quality validation.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..parsers import ClinVarParser, PubMedParser, HPOParser, UniProtParser
from ..normalizers import (
    GeneNormalizer,
    VariantNormalizer,
    PhenotypeNormalizer,
    PublicationNormalizer,
)
from ..mappers import GeneVariantMapper, VariantPhenotypeMapper, CrossReferenceMapper


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

        # Initialize transformation components
        self.parsers = {
            "clinvar": ClinVarParser(),
            "pubmed": PubMedParser(),
            "hpo": HPOParser(),
            "uniprot": UniProtParser(),
        }

        self.normalizers = {
            "gene": GeneNormalizer(),
            "variant": VariantNormalizer(),
            "phenotype": PhenotypeNormalizer(),
            "publication": PublicationNormalizer(),
        }

        self.mappers = {
            "gene_variant": GeneVariantMapper(),
            "variant_phenotype": VariantPhenotypeMapper(),
            "cross_reference": CrossReferenceMapper(),
        }

        # Results cache
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
        self, raw_data: Dict[str, List[Dict[str, Any]]], validate: bool = True
    ) -> Dict[str, Any]:
        """
        Transform data from all sources through the complete ETL pipeline.

        Args:
            raw_data: Dictionary mapping source names to lists of raw data
            validate: Whether to perform validation during transformation

        Returns:
            Dictionary with transformed data and metadata
        """
        start_time = time.time()

        results = {}
        all_errors = []

        try:
            # Stage 1: Parse all sources
            parsed_data = await self._parse_all_sources(raw_data)
            results["parsed"] = parsed_data

            # Stage 2: Normalize entities
            normalized_data = self._normalize_all_entities(parsed_data)
            results["normalized"] = normalized_data

            # Stage 3: Create cross-references
            mapped_data = self._create_cross_references(normalized_data)
            results["mapped"] = mapped_data

            # Stage 4: Validate if requested
            if validate:
                validation_results = self._validate_transformed_data(mapped_data)
                results["validation"] = validation_results
                all_errors.extend(validation_results.get("errors", []))

            # Stage 5: Export results
            export_results = self._export_transformed_data(results)
            results["export"] = export_results

            # Update metrics
            self._update_metrics(results, time.time() - start_time)

            results["metadata"] = {
                "processing_time_seconds": time.time() - start_time,
                "total_errors": len(all_errors),
                "errors": all_errors,
                "metrics": self._get_metrics_summary(),
            }

        except Exception as e:
            error_msg = f"ETL transformation failed: {str(e)}"
            all_errors.append(error_msg)
            results["error"] = error_msg

        return results

    async def _parse_all_sources(
        self, raw_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Parse data from all sources."""
        start_time = time.time()
        parsed_data = {}
        errors = []

        for source_name, source_data in raw_data.items():
            try:
                if source_name in self.parsers:
                    parser = self.parsers[source_name]
                    parsed_records = parser.parse_batch(source_data)
                    parsed_data[source_name] = parsed_records

                    # Validate parsed data
                    for record in parsed_records:
                        if hasattr(parser, "validate_parsed_data"):
                            validation_errors = parser.validate_parsed_data(record)
                            if validation_errors:
                                errors.extend(validation_errors)

                else:
                    errors.append(f"No parser available for source: {source_name}")

            except Exception as e:
                errors.append(f"Failed to parse {source_name}: {str(e)}")

        # Record results
        result = TransformationResult(
            stage=TransformationStage.PARSING,
            status=TransformationStatus.COMPLETED
            if not errors
            else TransformationStatus.PARTIAL,
            records_processed=sum(len(records) for records in parsed_data.values()),
            records_failed=len(errors),
            data=parsed_data,
            errors=errors,
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["parsing"] = result
        return parsed_data

    def _normalize_all_entities(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize entities from parsed data."""
        start_time = time.time()
        normalized_data = {
            "genes": [],
            "variants": [],
            "phenotypes": [],
            "publications": [],
        }
        errors = []

        # Normalize genes
        gene_records = self._extract_entity_records(parsed_data, "gene")
        for record in gene_records:
            normalized = self.normalizers["gene"].normalize(
                record, source=record.get("source", "unknown")
            )
            if normalized:
                normalized_data["genes"].append(normalized)
            else:
                errors.append(f"Failed to normalize gene: {record}")

        # Normalize variants
        variant_records = self._extract_entity_records(parsed_data, "variant")
        for record in variant_records:
            normalized = self.normalizers["variant"].normalize(
                record, source=record.get("source", "unknown")
            )
            if normalized:
                normalized_data["variants"].append(normalized)
            else:
                errors.append(f"Failed to normalize variant: {record}")

        # Normalize phenotypes
        phenotype_records = self._extract_entity_records(parsed_data, "phenotype")
        for record in phenotype_records:
            normalized = self.normalizers["phenotype"].normalize(
                record, source=record.get("source", "unknown")
            )
            if normalized:
                normalized_data["phenotypes"].append(normalized)
            else:
                errors.append(f"Failed to normalize phenotype: {record}")

        # Normalize publications
        publication_records = self._extract_entity_records(parsed_data, "publication")
        for record in publication_records:
            normalized = self.normalizers["publication"].normalize(
                record, source=record.get("source", "unknown")
            )
            if normalized:
                normalized_data["publications"].append(normalized)
            else:
                errors.append(f"Failed to normalize publication: {record}")

        # Record results
        result = TransformationResult(
            stage=TransformationStage.NORMALIZATION,
            status=TransformationStatus.COMPLETED
            if not errors
            else TransformationStatus.PARTIAL,
            records_processed=sum(len(records) for records in normalized_data.values()),
            records_failed=len(errors),
            data=normalized_data,
            errors=errors,
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["normalization"] = result
        return normalized_data

    def _extract_entity_records(
        self, parsed_data: Dict[str, Any], entity_type: str
    ) -> List[Dict[str, Any]]:
        """Extract entity records of specific type from parsed data."""
        records = []

        if entity_type == "gene":
            # Extract genes from UniProt and ClinVar data
            if "uniprot" in parsed_data:
                for record in parsed_data["uniprot"]:
                    if "genes" in record:
                        for gene in record["genes"]:
                            gene_copy = gene.copy()
                            gene_copy["source"] = "uniprot"
                            records.append(gene_copy)

            if "clinvar" in parsed_data:
                for record in parsed_data["clinvar"]:
                    if record.gene_symbol:
                        records.append(
                            {
                                "symbol": record.gene_symbol,
                                "name": record.gene_name,
                                "id": record.gene_id,
                                "source": "clinvar",
                            }
                        )

        elif entity_type == "variant":
            # Extract variants from ClinVar data
            if "clinvar" in parsed_data:
                # ClinVar records are already variant-centric
                for record in parsed_data["clinvar"]:
                    record_copy = {
                        "clinvar_id": record.clinvar_id,
                        "variant_id": record.variant_id,
                        "variation_name": record.variation_name,
                        "variant_type": record.variant_type.value
                        if record.variant_type
                        else None,
                        "clinical_significance": record.clinical_significance,
                        "chromosome": record.chromosome,
                        "start_position": record.start_position,
                        "reference_allele": record.reference_allele,
                        "alternate_allele": record.alternate_allele,
                        "source": "clinvar",
                    }
                    records.append(record_copy)

        elif entity_type == "phenotype":
            # Extract phenotypes from ClinVar and HPO data
            if "clinvar" in parsed_data:
                for record in parsed_data["clinvar"]:
                    for phenotype_name in record.phenotypes:
                        records.append({"name": phenotype_name, "source": "clinvar"})

            if "hpo" in parsed_data:
                # HPO records are already phenotype objects
                for record in parsed_data["hpo"]:
                    records.append(
                        {
                            "hpo_id": record.hpo_id,
                            "name": record.name,
                            "definition": record.definition,
                            "source": "hpo",
                        }
                    )

        elif entity_type == "publication":
            # Extract publications from PubMed and UniProt data
            if "pubmed" in parsed_data:
                # PubMed records are already publication objects
                for record in parsed_data["pubmed"]:
                    record_copy = {
                        "pubmed_id": record.pubmed_id,
                        "title": record.title,
                        "authors": [
                            author.last_name
                            for author in record.authors
                            if author.last_name
                        ],
                        "journal": record.journal.title if record.journal else None,
                        "publication_date": record.publication_date.isoformat()
                        if record.publication_date
                        else None,
                        "doi": record.doi,
                        "source": "pubmed",
                    }
                    records.append(record_copy)

            if "uniprot" in parsed_data:
                for record in parsed_data["uniprot"]:
                    if "references" in record:
                        for ref in record["references"]:
                            if ref.get("citation", {}).get("title"):
                                records.append(
                                    {
                                        "title": ref["citation"]["title"],
                                        "pubmed_id": ref.get("pubmedId"),
                                        "source": "uniprot",
                                    }
                                )

        return records

    def _create_cross_references(
        self, normalized_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create cross-references between normalized entities."""
        start_time = time.time()
        mapped_data = {}
        errors = []

        try:
            # Create gene-variant mappings
            gene_variant_links = []
            for gene in normalized_data["genes"]:
                for variant in normalized_data["variants"]:
                    # Add gene coordinates if available (simplified)
                    if hasattr(variant, "chromosome") and variant.get("chromosome"):
                        self.mappers["gene_variant"].add_gene_coordinates(
                            gene.primary_id,
                            variant["chromosome"],
                            gene.primary_id,  # Simplified - would need actual coordinates
                            gene.primary_id + 1000,
                        )

                    link = self.mappers["gene_variant"].map_gene_variant_relationship(
                        gene, variant
                    )
                    if link:
                        gene_variant_links.append(link)

            mapped_data["gene_variant_links"] = gene_variant_links

            # Create variant-phenotype mappings
            variant_phenotype_links = []
            for variant in normalized_data["variants"]:
                for phenotype in normalized_data["phenotypes"]:
                    # Create variant object for mapping
                    variant_obj = type(
                        "Variant",
                        (),
                        {
                            "primary_id": variant["clinvar_id"]
                            if "clinvar_id" in variant
                            else variant.get("variant_id", ""),
                            "clinical_significance": variant.get(
                                "clinical_significance"
                            ),
                            "source": variant.get("source", "unknown"),
                        },
                    )()

                    link = self.mappers[
                        "variant_phenotype"
                    ].map_variant_phenotype_relationship(variant_obj, phenotype)
                    if link:
                        variant_phenotype_links.append(link)

            mapped_data["variant_phenotype_links"] = variant_phenotype_links

            # Build cross-reference networks
            networks = {}
            for gene in normalized_data["genes"][:1]:  # Limit for testing
                if hasattr(gene, "symbol") and gene.symbol:
                    network = self.mappers[
                        "cross_reference"
                    ].build_cross_reference_network(gene.symbol)
                    networks[gene.symbol] = network

            mapped_data["networks"] = networks

        except Exception as e:
            errors.append(f"Cross-reference mapping failed: {str(e)}")

        # Record results
        result = TransformationResult(
            stage=TransformationStage.MAPPING,
            status=TransformationStatus.COMPLETED
            if not errors
            else TransformationStatus.PARTIAL,
            records_processed=len(mapped_data.get("gene_variant_links", []))
            + len(mapped_data.get("variant_phenotype_links", [])),
            records_failed=len(errors),
            data=mapped_data,
            errors=errors,
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["mapping"] = result
        return mapped_data

    def _validate_transformed_data(self, mapped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transformed data quality."""
        start_time = time.time()
        validation_results = {"passed": 0, "failed": 0, "errors": []}

        # Validate mappings
        for link in mapped_data.get("gene_variant_links", []):
            if hasattr(self.mappers["gene_variant"], "validate_mapping"):
                errors = self.mappers["gene_variant"].validate_mapping(link)
                if errors:
                    validation_results["failed"] += 1
                    validation_results["errors"].extend(errors)
                else:
                    validation_results["passed"] += 1

        for link in mapped_data.get("variant_phenotype_links", []):
            if hasattr(self.mappers["variant_phenotype"], "validate_mapping"):
                errors = self.mappers["variant_phenotype"].validate_mapping(link)
                if errors:
                    validation_results["failed"] += 1
                    validation_results["errors"].extend(errors)
                else:
                    validation_results["passed"] += 1

        # Record results
        result = TransformationResult(
            stage=TransformationStage.VALIDATION,
            status=TransformationStatus.COMPLETED,
            records_processed=validation_results["passed"]
            + validation_results["failed"],
            records_failed=validation_results["failed"],
            data=validation_results,
            errors=validation_results["errors"],
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["validation"] = result
        return validation_results

    def _export_transformed_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Export transformed data to files."""
        start_time = time.time()
        export_results = {"files_created": [], "errors": []}

        try:
            import json

            # Export normalized entities
            for entity_type, entities in results.get("normalized", {}).items():
                if entities:
                    filename = f"{entity_type}_normalized.json"
                    filepath = self.output_dir / filename

                    with open(filepath, "w") as f:
                        json.dump(
                            [
                                {
                                    "primary_id": e.primary_id,
                                    "name": getattr(
                                        e, "name", getattr(e, "symbol", "Unknown")
                                    ),
                                    "source": e.source,
                                    "confidence": e.confidence_score,
                                }
                                for e in entities
                            ],
                            f,
                            indent=2,
                            default=str,
                        )

                    export_results["files_created"].append(str(filepath))

            # Export mappings
            if "mapped" in results:
                mappings_file = self.output_dir / "entity_mappings.json"
                with open(mappings_file, "w") as f:
                    json.dump(
                        {
                            "gene_variant_count": len(
                                results["mapped"].get("gene_variant_links", [])
                            ),
                            "variant_phenotype_count": len(
                                results["mapped"].get("variant_phenotype_links", [])
                            ),
                            "networks_count": len(
                                results["mapped"].get("networks", {})
                            ),
                        },
                        f,
                        indent=2,
                    )

                export_results["files_created"].append(str(mappings_file))

        except Exception as e:
            export_results["errors"].append(f"Export failed: {str(e)}")

        # Record results
        result = TransformationResult(
            stage=TransformationStage.EXPORT,
            status=TransformationStatus.COMPLETED
            if not export_results["errors"]
            else TransformationStatus.FAILED,
            records_processed=len(export_results["files_created"]),
            records_failed=len(export_results["errors"]),
            data=export_results,
            errors=export_results["errors"],
            duration_seconds=time.time() - start_time,
            timestamp=time.time(),
        )

        self.results["export"] = result
        return export_results

    def _update_metrics(self, results: Dict[str, Any], total_time: float):
        """Update transformation metrics."""
        self.metrics.processing_time_seconds = total_time
        self.metrics.stage_metrics = {k: v.__dict__ for k, v in self.results.items()}

        # Count records
        if "parsed" in results:
            for source_data in results["parsed"].values():
                self.metrics.parsed_records += len(source_data)

        if "normalized" in results:
            for entity_list in results["normalized"].values():
                self.metrics.normalized_records += len(entity_list)

        if "mapped" in results:
            self.metrics.mapped_relationships = len(
                results["mapped"].get("gene_variant_links", [])
            ) + len(results["mapped"].get("variant_phenotype_links", []))

        if "validation" in results:
            self.metrics.validation_errors = results["validation"].get("failed", 0)

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
            Dictionary with status information
        """
        return {
            "stages": {k: v.status.value for k, v in self.results.items()},
            "metrics": self._get_metrics_summary(),
            "last_updated": max(
                (r.timestamp for r in self.results.values()), default=None
            ),
        }
