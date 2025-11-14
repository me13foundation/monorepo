"""
Unified Search Service for MED13 Resource Library.

Provides cross-entity search capabilities with relevance scoring and filtering.
"""

import logging
from enum import Enum

from src.application.services.evidence_service import EvidenceApplicationService
from src.application.services.gene_service import GeneApplicationService
from src.application.services.phenotype_service import PhenotypeApplicationService
from src.application.services.variant_service import VariantApplicationService
from src.domain.entities.evidence import Evidence
from src.domain.entities.gene import Gene
from src.domain.entities.phenotype import Phenotype
from src.domain.entities.variant import Variant
from src.type_definitions.common import JSONObject, QueryFilters, clone_query_filters


class SearchEntity(str, Enum):
    """Searchable entities in the system."""

    GENES = "genes"
    VARIANTS = "variants"
    PHENOTYPES = "phenotypes"
    EVIDENCE = "evidence"
    ALL = "all"


class SearchResultType(str, Enum):
    """Type of search result."""

    GENE = "gene"
    VARIANT = "variant"
    PHENOTYPE = "phenotype"
    EVIDENCE = "evidence"


logger = logging.getLogger(__name__)


class SearchResult:
    """Container for search result with scoring."""

    def __init__(  # noqa: PLR0913
        self,
        entity_type: SearchResultType,
        entity_id: str | int,
        title: str,
        description: str,
        relevance_score: float,
        metadata: JSONObject | None = None,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.title = title
        self.description = description
        self.relevance_score = relevance_score
        if metadata is not None:
            metadata_payload: JSONObject = dict(metadata)
        else:
            metadata_payload = {}
        self.metadata = metadata_payload

    def to_dict(self) -> JSONObject:
        """Convert to dictionary for API response."""
        return {
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "title": self.title,
            "description": self.description,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


class UnifiedSearchService:
    """
    Unified search service that aggregates search across all entities.

    Provides relevance scoring, filtering, and cross-entity search capabilities.
    """

    def __init__(
        self,
        gene_service: GeneApplicationService,
        variant_service: VariantApplicationService,
        phenotype_service: PhenotypeApplicationService,
        evidence_service: EvidenceApplicationService,
    ):
        """
        Initialize the unified search service.

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

    def search(
        self,
        query: str,
        entity_types: list[SearchEntity] | None = None,
        limit: int = 20,
        filters: QueryFilters | None = None,
    ) -> JSONObject:
        """
        Perform unified search across specified entities.

        Args:
            query: Search query string
            entity_types: List of entity types to search (defaults to all)
            limit: Maximum results per entity type
            filters: Additional filters to apply

        Returns:
            Search results organized by entity type
        """
        if not query or not query.strip():
            return {"query": query, "results": [], "total_results": 0}

        # Default to searching all entities if none specified
        if entity_types is None:
            entity_types = [SearchEntity.ALL]

        # Normalize entity types
        if SearchEntity.ALL in entity_types:
            entity_types = [
                SearchEntity.GENES,
                SearchEntity.VARIANTS,
                SearchEntity.PHENOTYPES,
                SearchEntity.EVIDENCE,
            ]

        results = []
        total_results = 0

        # Search genes
        if SearchEntity.GENES in entity_types:
            gene_results = self._search_genes(query, limit, filters)
            results.extend(gene_results)
            total_results += len(gene_results)

        # Search variants
        if SearchEntity.VARIANTS in entity_types:
            variant_results = self._search_variants(query, limit, filters)
            results.extend(variant_results)
            total_results += len(variant_results)

        # Search phenotypes
        if SearchEntity.PHENOTYPES in entity_types:
            phenotype_results = self._search_phenotypes(query, limit, filters)
            results.extend(phenotype_results)
            total_results += len(phenotype_results)

        # Search evidence
        if SearchEntity.EVIDENCE in entity_types:
            evidence_results = self._search_evidence(query, limit, filters)
            results.extend(evidence_results)
            total_results += len(evidence_results)

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return {
            "query": query,
            "results": [result.to_dict() for result in results],
            "total_results": total_results,
            "entity_breakdown": self._get_entity_breakdown(results),
        }

    def _search_genes(
        self,
        query: str,
        limit: int,
        _filters: QueryFilters | None,
    ) -> list[SearchResult]:
        """Search genes and convert to search results."""
        try:
            genes = self._gene_service.search_genes(query, limit)
        except Exception as exc:  # noqa: BLE001 - defensive fallback
            logger.warning("Gene search failed: %s", exc)
            return []

        results: list[SearchResult] = []
        for gene in genes:
            score = self._calculate_gene_relevance(query, gene)
            results.append(
                SearchResult(
                    entity_type=SearchResultType.GENE,
                    entity_id=gene.gene_id,
                    title=f"{gene.symbol} ({gene.name})",
                    description=gene.description
                    or f"Gene located on chromosome {gene.chromosome}",
                    relevance_score=score,
                    metadata={
                        "symbol": gene.symbol,
                        "chromosome": gene.chromosome,
                        "gene_type": gene.gene_type,
                    },
                ),
            )

        return results

    def _search_variants(
        self,
        query: str,
        limit: int,
        filters: QueryFilters | None,
    ) -> list[SearchResult]:
        """Search variants and convert to search results."""
        try:
            # Use the paginate method with filters
            filters_dict = self._clone_filters(filters)
            # Add search query to filters if provided
            if query:
                filters_dict["search"] = query

            variants, _ = self._variant_service.list_variants(
                page=1,
                per_page=limit,
                sort_by="variant_id",
                sort_order="asc",
                filters=filters_dict or None,
            )
        except Exception as exc:  # noqa: BLE001 - defensive fallback
            logger.warning("Variant search failed: %s", exc)
            return []

        results: list[SearchResult] = []
        for variant in variants:
            score = self._calculate_variant_relevance(query, variant)
            entity_id = variant.id if variant.id is not None else 0
            results.append(
                SearchResult(
                    entity_type=SearchResultType.VARIANT,
                    entity_id=entity_id,
                    title=f"{variant.variant_id} - {variant.chromosome}:{variant.position}",
                    description=(
                        f"{variant.variant_type} variant with {variant.clinical_significance} significance"
                    ),
                    relevance_score=score,
                    metadata={
                        "chromosome": variant.chromosome,
                        "position": variant.position,
                        "clinical_significance": variant.clinical_significance,
                        "gene_symbol": variant.gene_symbol,
                    },
                ),
            )

        return results

    def _search_phenotypes(
        self,
        query: str,
        limit: int,
        filters: QueryFilters | None,
    ) -> list[SearchResult]:
        """Search phenotypes and convert to search results."""
        try:
            phenotypes = self._phenotype_service.search_phenotypes(
                query,
                limit,
                filters,
            )
        except Exception as exc:  # noqa: BLE001 - defensive fallback
            logger.warning("Phenotype search failed: %s", exc)
            return []

        results: list[SearchResult] = []
        for phenotype in phenotypes:
            score = self._calculate_phenotype_relevance(query, phenotype)
            entity_id = phenotype.id if phenotype.id is not None else 0
            results.append(
                SearchResult(
                    entity_type=SearchResultType.PHENOTYPE,
                    entity_id=entity_id,
                    title=f"{phenotype.name} ({phenotype.identifier.hpo_id})",
                    description=phenotype.definition
                    or f"{phenotype.category} phenotype",
                    relevance_score=score,
                    metadata={
                        "hpo_id": phenotype.identifier.hpo_id,
                        "category": phenotype.category,
                        "synonyms": (
                            list(phenotype.synonyms) if phenotype.synonyms else []
                        ),
                    },
                ),
            )

        return results

    def _search_evidence(
        self,
        query: str,
        limit: int,
        filters: QueryFilters | None,
    ) -> list[SearchResult]:
        """Search evidence and convert to search results."""
        try:
            evidence_list = self._evidence_service.search_evidence(
                query,
                limit,
                filters,
            )
        except Exception as exc:  # noqa: BLE001 - defensive fallback
            logger.warning("Evidence search failed: %s", exc)
            return []

        snippet_len = 200
        results: list[SearchResult] = []
        for evidence in evidence_list:
            score = self._calculate_evidence_relevance(query, evidence)
            entity_id = evidence.id if evidence.id is not None else 0
            description = (
                evidence.description[:snippet_len] + "..."
                if len(evidence.description) > snippet_len
                else evidence.description
            )
            results.append(
                SearchResult(
                    entity_type=SearchResultType.EVIDENCE,
                    entity_id=entity_id,
                    title=f"Evidence #{entity_id} ({evidence.evidence_level.value})",
                    description=description,
                    relevance_score=score,
                    metadata={
                        "evidence_level": evidence.evidence_level.value,
                        "evidence_type": evidence.evidence_type,
                        "confidence_score": evidence.confidence.score,
                        "variant_id": evidence.variant_id,
                        "phenotype_id": evidence.phenotype_id,
                    },
                ),
            )

        return results

    def _calculate_gene_relevance(self, query: str, gene: Gene) -> float:
        """Calculate relevance score for gene search result."""
        query_lower = query.lower()
        score = 0.0

        # Exact symbol match gets highest score
        if query_lower == gene.symbol.lower():
            score += 1.0

        # Symbol starts with query
        elif gene.symbol.lower().startswith(query_lower):
            score += 0.8

        # Symbol contains query
        elif query_lower in gene.symbol.lower():
            score += 0.6

        # Name contains query
        if query_lower in (gene.name or "").lower():
            score += 0.4

        # Description contains query
        if query_lower in (gene.description or "").lower():
            score += 0.2

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_variant_relevance(self, query: str, variant: Variant) -> float:
        """Calculate relevance score for variant search result."""
        query_lower = query.lower()
        score = 0.0

        # Variant ID exact match
        if query_lower == (variant.variant_id or "").lower():
            score += 1.0

        # Variant ID contains query
        elif query_lower in (variant.variant_id or "").lower():
            score += 0.7

        # Gene symbol match
        if query_lower == (variant.gene_symbol or "").lower():
            score += 0.8
        elif query_lower in (variant.gene_symbol or "").lower():
            score += 0.5

        # Clinical significance match
        if query_lower in (variant.clinical_significance or "").lower():
            score += 0.3

        return min(score, 1.0)

    def _calculate_phenotype_relevance(self, query: str, phenotype: Phenotype) -> float:
        """Calculate relevance score for phenotype search result."""
        query_lower = query.lower()
        score = 0.0

        # HPO ID exact match
        if query_lower == phenotype.identifier.hpo_id.lower():
            score += 1.0

        # HPO term exact match
        if query_lower == phenotype.identifier.hpo_term.lower():
            score += 0.9

        # Name exact match
        if query_lower == phenotype.name.lower():
            score += 0.8

        # Name contains query
        elif query_lower in phenotype.name.lower():
            score += 0.6

        # Synonyms contain query
        for synonym in phenotype.synonyms:
            if query_lower in synonym.lower():
                score += 0.5
                break

        # Definition contains query
        if query_lower in (phenotype.definition or "").lower():
            score += 0.3

        return min(score, 1.0)

    def _calculate_evidence_relevance(self, query: str, evidence: Evidence) -> float:
        """Calculate relevance score for evidence search result."""
        query_lower = query.lower()
        score = 0.0

        # Description contains query (highest weight for evidence)
        if query_lower in evidence.description.lower():
            score += 0.8

        # Summary contains query
        if query_lower in (evidence.summary or "").lower():
            score += 0.6

        # Evidence type match
        if query_lower in evidence.evidence_type.lower():
            score += 0.3

        # Study type match
        if query_lower in (evidence.study_type or "").lower():
            score += 0.2

        return min(score, 1.0)

    def _get_entity_breakdown(self, results: list[SearchResult]) -> dict[str, int]:
        """Get count breakdown by entity type."""
        breakdown: dict[str, int] = {}
        for result in results:
            entity_type = result.entity_type.value
            breakdown[entity_type] = breakdown.get(entity_type, 0) + 1
        return breakdown

    @staticmethod
    def _clone_filters(filters: QueryFilters | None) -> QueryFilters:
        return clone_query_filters(filters) or {}


__all__ = ["SearchEntity", "SearchResult", "SearchResultType", "UnifiedSearchService"]
