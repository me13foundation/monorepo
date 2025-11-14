"""
Curation Service for MED13 Resource Library.

Provides clinical data enrichment for curation workflows.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from src.application.curation.repositories.review_repository import (
    ReviewFilter,
    ReviewRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.application.curation.repositories.review_repository import ReviewRecordLike
    from src.application.services.evidence_service import EvidenceApplicationService
    from src.application.services.phenotype_service import PhenotypeApplicationService
    from src.application.services.variant_service import VariantApplicationService
    from src.domain.entities.evidence import Evidence
    from src.domain.entities.variant import Variant
    from src.type_definitions.common import QueryFilters

logger = logging.getLogger(__name__)


class CurationService:
    """
    Service for curation workflows that enriches review data with clinical context.

    Provides clinical data enrichment for the curation dashboard, combining review
    metadata with actual clinical information for informed decision making.
    """

    def __init__(
        self,
        review_repository: ReviewRepository,
        variant_service: VariantApplicationService,
        evidence_service: EvidenceApplicationService,
        phenotype_service: PhenotypeApplicationService,
    ):
        """
        Initialize the curation service.

        Args:
            review_repository: Repository for review records
            variant_service: Service for variant data
            evidence_service: Service for evidence data
            phenotype_service: Service for phenotype data
        """
        self._review_repository = review_repository
        self._variant_service = variant_service
        self._evidence_service = evidence_service
        self._phenotype_service = phenotype_service

    @dataclass(frozen=True)
    class ReviewQueueQuery:
        entity_type: str = "variants"
        status: str = "pending"
        priority: str | None = None
        clinical_filters: dict[str, Any] | None = None
        limit: int = 50
        offset: int = 0

    def get_enriched_review_queue(
        self,
        db: Session,
        query: ReviewQueueQuery | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Get enriched review queue with clinical data for curation.

        Args:
            db: Database session
            query: Query parameters (entity_type, filters, pagination)

        Returns:
            Tuple of (enriched_review_items, total_count)
        """
        # Get basic review records
        request = query or self.ReviewQueueQuery()
        review_records = self._review_repository.list_records(
            db,
            ReviewFilter(
                entity_type=request.entity_type,
                status=request.status,
                priority=request.priority,
            ),
            limit=request.limit,
            offset=request.offset,
        )

        # Enrich with clinical data
        enriched_items = []
        for review_record in review_records:
            if request.entity_type == "variants":
                enriched_item = self._enrich_variant_review(
                    review_record,
                    request.clinical_filters,
                )
            elif request.entity_type == "genes":
                enriched_item = self._enrich_gene_review(
                    review_record,
                    request.clinical_filters,
                )
            else:
                # Basic enrichment for other entity types
                enriched_item = self._create_basic_enrichment(review_record)

            if enriched_item:
                enriched_items.append(enriched_item)

        return enriched_items, len(enriched_items)

    def get_variant_clinical_details(self, variant_id: int) -> dict[str, Any] | None:
        """
        Get comprehensive clinical details for a specific variant.

        Args:
            db: Database session
            variant_id: Variant database ID

        Returns:
            Dictionary with comprehensive clinical information
        """
        # Get variant details
        variant_filters: QueryFilters = {"id": variant_id}
        variants, _ = self._variant_service.list_variants(
            page=1,
            per_page=1,
            sort_by="id",
            sort_order="asc",
            filters=variant_filters,
        )

        if not variants:
            return None

        variant = variants[0]

        # Get evidence records
        evidence_filters: QueryFilters = {"variant_id": variant_id}
        evidence_records = self._evidence_service.search_evidence(
            query="",
            limit=100,
            filters=evidence_filters,
        )

        # Get phenotypes associated with evidence
        phenotype_ids = list(
            {ev.phenotype_id for ev in evidence_records if ev.phenotype_id is not None},
        )
        phenotypes: list[dict[str, Any]] = []
        for phenotype_id in phenotype_ids[:10]:  # Limit to 10 phenotypes
            phenotype_filters: QueryFilters | None = self._build_filter(
                "id",
                phenotype_id,
            )
            if phenotype_filters is None:
                continue
            phenotype_list, _ = self._phenotype_service.list_phenotypes(
                page=1,
                per_page=1,
                sort_by="id",
                sort_order="asc",
                filters=phenotype_filters,
            )
            if not phenotype_list:
                continue
            phenotype_data = phenotype_list[0]
            phenotypes.append(
                {
                    "id": phenotype_id,
                    "name": phenotype_data.name,
                    "hpo_id": phenotype_data.identifier.hpo_id,
                    "definition": phenotype_data.definition,
                    "category": phenotype_data.category,
                },
            )

        max_publications = 5
        abstract_snippet_length = 300
        publications = [
            {
                "id": evidence.publication_id,
                "title": f"Publication {evidence.publication_id}",
                "authors": "Unknown",
                "journal": "Unknown",
                "year": "Unknown",
                "doi": "Unknown",
                "abstract": (
                    f"{evidence.description[:abstract_snippet_length]}..."
                    if len(evidence.description) > abstract_snippet_length
                    else evidence.description
                ),
            }
            for evidence in evidence_records[:max_publications]
            if evidence.publication_id
        ]

        return {
            "id": variant.id,
            "variant_id": variant.identifier.variant_id,
            "gene_symbol": (
                variant.gene_identifier.symbol if variant.gene_identifier else "Unknown"
            ),
            "chromosome": variant.chromosome,
            "position": variant.position,
            "reference_allele": variant.reference_allele,
            "alternate_allele": variant.alternate_allele,
            "clinical_significance": variant.clinical_significance,
            "hgvs_genomic": variant.hgvs_genomic,
            "hgvs_cdna": variant.hgvs_cdna,
            "hgvs_protein": variant.hgvs_protein,
            "confidence_score": self._calculate_confidence_score(evidence_records),
            "evidence_count": len(evidence_records),
            "evidence_levels": list(
                {ev.evidence_level.value for ev in evidence_records},
            ),
            "evidence_records": [
                {
                    "id": ev.id,
                    "evidence_level": ev.evidence_level.value,
                    "evidence_type": ev.evidence_type,
                    "description": ev.description,
                    "confidence": ev.confidence.score if ev.confidence else 0.5,
                    "variant_id": ev.variant_id,
                    "phenotype_id": ev.phenotype_id,
                }
                for ev in evidence_records
            ],
            "phenotypes": phenotypes,
            "publications": publications,
            "gnomad_af": variant.gnomad_af,
            "allele_frequency": variant.allele_frequency,
            "quality_score": 0.85,  # Placeholder - calculated in validation
            "issues": 0,  # Placeholder - from validation results
            "review_status": variant.review_status,
        }

    def _enrich_variant_review(
        self,
        review_record: ReviewRecordLike,
        clinical_filters: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Enrich a variant review record with clinical data."""
        # Get variant details
        raw_entity_id = review_record.get("entity_id")
        entity_identifier: str | int | None
        if isinstance(raw_entity_id, (str, int)):
            entity_identifier = raw_entity_id
        else:
            entity_identifier = None

        variant_filters = self._build_filter("id", entity_identifier)
        variants, _ = self._variant_service.list_variants(
            page=1,
            per_page=1,
            sort_by="id",
            sort_order="asc",
            filters=variant_filters,
        )

        if not variants:
            return None

        variant = variants[0]

        # Get evidence summary
        evidence_filters = self._build_filter("variant_id", entity_identifier)
        evidence_records = self._evidence_service.search_evidence(
            query="",
            limit=50,
            filters=evidence_filters,
        )

        # Extract evidence levels
        evidence_levels = list({ev.evidence_level.value for ev in evidence_records})

        # Get phenotype summary (simplified)
        phenotype_ids = list({ev.phenotype_id for ev in evidence_records})
        phenotypes = []
        for phenotype_id in phenotype_ids[:3]:  # Limit for card display
            phenotype_filters = self._build_filter("id", phenotype_id)
            if phenotype_filters is None:
                continue
            phenotype_list, _ = self._phenotype_service.list_phenotypes(
                page=1,
                per_page=1,
                sort_by="id",
                sort_order="asc",
                filters=phenotype_filters,
            )
            if phenotype_list:
                phenotype_data = phenotype_list[0]
                phenotypes.append(
                    {
                        "id": phenotype_id,
                        "name": phenotype_data.name,
                        "hpo_id": phenotype_data.identifier.hpo_id,
                    },
                )

        # Apply clinical filters if provided
        if clinical_filters and not self._passes_clinical_filters(
            variant,
            evidence_records,
            clinical_filters,
        ):
            return None

        lu = review_record.get("last_updated")
        last_updated_value = (
            lu.isoformat()
            if isinstance(lu, datetime)
            else (str(lu) if lu is not None else None)
        )

        return {
            "id": review_record.get("id"),
            "entity_id": review_record.get("entity_id"),
            "variant_id": variant.identifier.variant_id,
            "gene_symbol": (
                variant.gene_identifier.symbol if variant.gene_identifier else "Unknown"
            ),
            "chromosome": variant.chromosome,
            "position": variant.position,
            "clinical_significance": variant.clinical_significance,
            "confidence_score": self._calculate_confidence_score(evidence_records),
            "evidence_count": len(evidence_records),
            "evidence_levels": evidence_levels,
            "phenotypes": phenotypes,
            "gnomad_af": variant.gnomad_af,
            "allele_frequency": variant.allele_frequency,
            "quality_score": review_record.get("quality_score") or 0.85,
            "issues": review_record.get("issues", 0),
            "status": review_record.get("status", ""),
            "priority": review_record.get("priority", ""),
            "last_updated": last_updated_value,
        }

    def _enrich_gene_review(
        self,
        review_record: ReviewRecordLike,
        _clinical_filters: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Enrich a gene review record with clinical data."""
        # Placeholder for gene enrichment - would need gene service
        lu = review_record.get("last_updated")
        last_updated_value = (
            lu.isoformat()
            if isinstance(lu, datetime)
            else (str(lu) if lu is not None else None)
        )

        return {
            "id": review_record.get("id"),
            "entity_id": review_record.get("entity_id"),
            "gene_symbol": f"Gene_{review_record.get('entity_id')}",
            "quality_score": review_record.get("quality_score") or 0.8,
            "issues": review_record.get("issues", 0),
            "status": review_record.get("status", ""),
            "priority": review_record.get("priority", ""),
            "last_updated": last_updated_value,
        }

    def _create_basic_enrichment(
        self,
        review_record: ReviewRecordLike,
    ) -> dict[str, Any]:
        """Create basic enrichment for unsupported entity types."""
        lu = review_record.get("last_updated")
        last_updated_value = (
            lu.isoformat()
            if isinstance(lu, datetime)
            else (str(lu) if lu is not None else None)
        )

        return {
            "id": review_record.get("id"),
            "entity_id": review_record.get("entity_id"),
            "entity_type": review_record.get("entity_type", ""),
            "quality_score": review_record.get("quality_score") or 0.5,
            "issues": review_record.get("issues", 0),
            "status": review_record.get("status", ""),
            "priority": review_record.get("priority", ""),
            "last_updated": last_updated_value,
        }

    @staticmethod
    def _build_filter(
        key: str,
        value: object,
    ) -> QueryFilters | None:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return {key: value}
        return None

    def _calculate_confidence_score(self, evidence_records: list[Evidence]) -> float:
        """Calculate overall confidence score from evidence."""
        if not evidence_records:
            return 0.1

        # Simple scoring based on evidence levels and count
        level_scores = {
            "definitive": 1.0,
            "strong": 0.8,
            "supporting": 0.6,
            "limited": 0.3,
        }

        total_score = 0.0
        count = 0

        for evidence in evidence_records:
            level = evidence.evidence_level.value
            score = level_scores.get(level, 0.5)
            confidence = evidence.confidence.score if evidence.confidence else 0.5
            total_score += score * confidence
            count += 1

        return min(total_score / count if count > 0 else 0.1, 1.0)

    def _passes_clinical_filters(
        self,
        variant: Variant,
        evidence_records: list[Evidence],
        filters: dict[str, Any],
    ) -> bool:
        """Check if variant passes clinical filters."""
        # Clinical significance filter
        if "clinical_significance" in filters:
            sig_filter = filters["clinical_significance"]
            if (
                isinstance(sig_filter, list)
                and variant.clinical_significance not in sig_filter
            ):
                return False

        # Evidence level filter
        if "evidence_level" in filters:
            min_level = filters["evidence_level"]
            level_hierarchy = {
                "limited": 0,
                "supporting": 1,
                "strong": 2,
                "definitive": 3,
            }
            min_level_value = level_hierarchy.get(min_level, 0)

            has_required_level = any(
                level_hierarchy.get(ev.evidence_level.value, 0) >= min_level_value
                for ev in evidence_records
            )
            if not has_required_level:
                return False

        # Confidence filter
        if "confidence" in filters:
            confidence = self._calculate_confidence_score(evidence_records)
            if confidence < filters["confidence"]:
                return False

        return True


__all__ = ["CurationService"]
