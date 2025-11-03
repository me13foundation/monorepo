"""
Curation Service for MED13 Resource Library.

Provides clinical data enrichment for curation workflows.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.application.curation.repositories.review_repository import (
    ReviewRepository,
    ReviewFilter,
)
from src.models.database.review import ReviewRecord
from src.application.services.variant_service import VariantApplicationService
from src.application.services.evidence_service import EvidenceApplicationService
from src.application.services.phenotype_service import PhenotypeApplicationService
from src.domain.entities.evidence import Evidence
from src.domain.entities.variant import Variant


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

    def get_enriched_review_queue(
        self,
        db: Session,
        entity_type: str = "variants",
        status: str = "pending",
        priority: Optional[str] = None,
        clinical_filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get enriched review queue with clinical data for curation.

        Args:
            db: Database session
            entity_type: Type of entity to review (variants, genes, etc.)
            status: Review status filter
            priority: Priority filter
            clinical_filters: Additional clinical filters
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            Tuple of (enriched_review_items, total_count)
        """
        # Get basic review records
        review_records = self._review_repository.list(
            db,
            ReviewFilter(
                entity_type=entity_type,
                status=status,
                priority=priority,
            ),
            limit=limit,
            offset=offset,
        )

        # Enrich with clinical data
        enriched_items = []
        for review_record in review_records:
            if entity_type == "variants":
                enriched_item = self._enrich_variant_review(
                    review_record, clinical_filters
                )
            elif entity_type == "genes":
                enriched_item = self._enrich_gene_review(
                    review_record, clinical_filters
                )
            else:
                # Basic enrichment for other entity types
                enriched_item = self._create_basic_enrichment(review_record)

            if enriched_item:
                enriched_items.append(enriched_item)

        return enriched_items, len(enriched_items)

    def get_variant_clinical_details(
        self, db: Session, variant_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive clinical details for a specific variant.

        Args:
            db: Database session
            variant_id: Variant database ID

        Returns:
            Dictionary with comprehensive clinical information
        """
        try:
            # Get variant details
            variants, _ = self._variant_service.list_variants(
                page=1,
                per_page=1,
                sort_by="id",
                sort_order="asc",
                filters={"id": variant_id},
            )

            if not variants:
                return None

            variant = variants[0]

            # Get evidence records
            evidence_records = self._evidence_service.search_evidence(
                query="", limit=100, filters={"variant_id": variant_id}
            )

            # Get phenotypes associated with evidence
            phenotype_ids = list(set(ev.phenotype_id for ev in evidence_records))
            phenotypes = []
            for phenotype_id in phenotype_ids[:10]:  # Limit to 10 phenotypes
                phenotype_list, _ = self._phenotype_service.list_phenotypes(
                    page=1,
                    per_page=1,
                    sort_by="id",
                    sort_order="asc",
                    filters={"id": phenotype_id},
                )
                if phenotype_list:
                    phenotype_data = phenotype_list[0]
                    phenotypes.append(
                        {
                            "id": phenotype_id,
                            "name": phenotype_data.name,
                            "hpo_id": phenotype_data.identifier.hpo_id,
                            "definition": phenotype_data.definition,
                            "category": phenotype_data.category,
                        }
                    )

            # Get publications (simplified - would need publication service)
            publications = []
            for evidence in evidence_records[:5]:  # Limit to 5 publications
                if evidence.publication_id:
                    publications.append(
                        {
                            "id": evidence.publication_id,
                            "title": f"Publication {evidence.publication_id}",
                            "authors": "Unknown",
                            "journal": "Unknown",
                            "year": "Unknown",
                            "doi": "Unknown",
                            "abstract": (
                                evidence.description[:300] + "..."
                                if len(evidence.description) > 300
                                else evidence.description
                            ),
                        }
                    )

            # Build comprehensive clinical data
            clinical_data = {
                "id": variant.id,
                "variant_id": variant.identifier.variant_id,
                "gene_symbol": (
                    variant.gene_identifier.symbol
                    if variant.gene_identifier
                    else "Unknown"
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
                    set(ev.evidence_level.value for ev in evidence_records)
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
                "quality_score": 0.85,  # Placeholder - would be calculated from validation
                "issues": 0,  # Placeholder - would be from validation results
                "review_status": variant.review_status,
            }

            return clinical_data

        except Exception as e:
            print(f"Error getting clinical details for variant {variant_id}: {e}")
            return None

    def _enrich_variant_review(
        self,
        review_record: ReviewRecord,
        clinical_filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Enrich a variant review record with clinical data."""
        try:
            # Get variant details
            variants, _ = self._variant_service.list_variants(
                page=1,
                per_page=1,
                sort_by="id",
                sort_order="asc",
                filters={"id": review_record.entity_id},
            )

            if not variants:
                return None

            variant = variants[0]

            # Get evidence summary
            evidence_records = self._evidence_service.search_evidence(
                query="", limit=50, filters={"variant_id": review_record.entity_id}
            )

            # Extract evidence levels
            evidence_levels = list(
                set(ev.evidence_level.value for ev in evidence_records)
            )

            # Get phenotype summary (simplified)
            phenotype_ids = list(set(ev.phenotype_id for ev in evidence_records))
            phenotypes = []
            for phenotype_id in phenotype_ids[:3]:  # Limit for card display
                phenotype_list, _ = self._phenotype_service.list_phenotypes(
                    page=1,
                    per_page=1,
                    sort_by="id",
                    sort_order="asc",
                    filters={"id": phenotype_id},
                )
                if phenotype_list:
                    phenotype_data = phenotype_list[0]
                    phenotypes.append(
                        {
                            "id": phenotype_id,
                            "name": phenotype_data.name,
                            "hpo_id": phenotype_data.identifier.hpo_id,
                        }
                    )

            # Apply clinical filters if provided
            if clinical_filters:
                if not self._passes_clinical_filters(
                    variant, evidence_records, clinical_filters
                ):
                    return None

            return {
                "id": review_record.id,
                "entity_id": review_record.entity_id,
                "variant_id": variant.identifier.variant_id,
                "gene_symbol": (
                    variant.gene_identifier.symbol
                    if variant.gene_identifier
                    else "Unknown"
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
                "quality_score": review_record.quality_score or 0.85,
                "issues": review_record.issues,
                "status": review_record.status,
                "priority": review_record.priority,
                "last_updated": (
                    review_record.last_updated.isoformat()
                    if review_record.last_updated
                    else None
                ),
            }

        except Exception as e:
            print(f"Error enriching variant review {review_record.id}: {e}")
            return None

    def _enrich_gene_review(
        self,
        review_record: ReviewRecord,
        clinical_filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Enrich a gene review record with clinical data."""
        # Placeholder for gene enrichment - would need gene service
        return {
            "id": review_record.id,
            "entity_id": review_record.entity_id,
            "gene_symbol": f"Gene_{review_record.entity_id}",
            "quality_score": review_record.quality_score or 0.8,
            "issues": review_record.issues,
            "status": review_record.status,
            "priority": review_record.priority,
            "last_updated": (
                review_record.last_updated.isoformat()
                if review_record.last_updated
                else None
            ),
        }

    def _create_basic_enrichment(self, review_record: ReviewRecord) -> Dict[str, Any]:
        """Create basic enrichment for unsupported entity types."""
        return {
            "id": review_record.id,
            "entity_id": review_record.entity_id,
            "entity_type": review_record.entity_type,
            "quality_score": review_record.quality_score or 0.5,
            "issues": review_record.issues,
            "status": review_record.status,
            "priority": review_record.priority,
            "last_updated": (
                review_record.last_updated.isoformat()
                if review_record.last_updated
                else None
            ),
        }

    def _calculate_confidence_score(self, evidence_records: List[Evidence]) -> float:
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
        evidence_records: List[Evidence],
        filters: Dict[str, Any],
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
