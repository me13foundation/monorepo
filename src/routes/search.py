"""
Unified Search API routes for MED13 Resource Library.

Provides cross-entity search capabilities with relevance scoring.
"""

from typing import TypedDict, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.application.search.search_service import (
    SearchEntity,
    SearchResultType,
    UnifiedSearchService,
)
from src.database.session import get_session
from src.infrastructure.dependency_injection.container import (
    get_legacy_dependency_container,
)
from src.type_definitions.common import JSONObject

router = APIRouter(prefix="/search", tags=["search"])


class RawSearchResult(TypedDict):
    """Raw search result payload from the service."""

    entity_type: str
    entity_id: int | str
    title: str
    description: str
    relevance_score: float
    metadata: JSONObject


class UnifiedSearchPayload(TypedDict, total=False):
    """Typed representation of the unified search payload."""

    query: str
    total_results: int
    entity_breakdown: dict[str, int]
    results: list[RawSearchResult]


class SearchResultItem(BaseModel):
    """Typed representation of a unified search result."""

    entity_type: SearchResultType
    entity_id: str
    title: str
    description: str
    relevance_score: float = Field(ge=0.0)
    metadata: JSONObject


class UnifiedSearchResponse(BaseModel):
    """Unified search response payload."""

    query: str
    total_results: int
    entity_breakdown: dict[str, int]
    results: list[SearchResultItem]


class SearchSuggestionResponse(BaseModel):
    """Search suggestion payload."""

    query: str
    suggestions: list[str]
    total_suggestions: int


class SearchStatisticsResponse(BaseModel):
    """Search statistics payload."""

    total_entities: dict[str, int]
    searchable_fields: dict[str, list[str]]
    last_updated: str | None = None


def get_search_service(db: Session = Depends(get_session)) -> "UnifiedSearchService":
    """Dependency injection for unified search service."""
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_unified_search_service(db)


@router.post(
    "/",
    summary="Unified search across all entities",
    response_model=UnifiedSearchResponse,
)
async def unified_search(
    query: str = Query(..., min_length=1, max_length=200, description="Search query"),
    entity_types: list[SearchEntity]
    | None = Query(
        None,
        description="Entity types to search (defaults to all)",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per entity type"),
    service: UnifiedSearchService = Depends(get_search_service),
) -> UnifiedSearchResponse:
    """
    Perform unified search across genes, variants, phenotypes, and evidence.

    Returns results sorted by relevance score with metadata for each entity type.
    """
    try:
        raw = service.search(
            query=query,
            entity_types=entity_types,
            limit=limit,
        )

        payload = cast("UnifiedSearchPayload", raw)
        raw_results = payload.get("results")
        results_payload: list[RawSearchResult] = (
            raw_results if isinstance(raw_results, list) else []
        )

        result_items = [
            SearchResultItem(
                entity_type=SearchResultType(item["entity_type"]),
                entity_id=str(item["entity_id"]),
                title=item["title"],
                description=item["description"],
                relevance_score=float(item["relevance_score"]),
                metadata=item["metadata"],
            )
            for item in results_payload
        ]

        query_value = payload.get("query")
        if not isinstance(query_value, str):
            query_value = query

        total_results_value = payload.get("total_results")
        if not isinstance(total_results_value, int):
            total_results_value = len(result_items)

        breakdown_value = payload.get("entity_breakdown")
        if not isinstance(breakdown_value, dict):
            breakdown_value = {}

        return UnifiedSearchResponse(
            query=query_value,
            total_results=total_results_value,
            entity_breakdown=breakdown_value,
            results=result_items,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}")


@router.get(
    "/suggest",
    summary="Search suggestions",
    response_model=SearchSuggestionResponse,
)
async def search_suggestions(
    query: str = Query(
        ...,
        min_length=1,
        max_length=50,
        description="Partial search query",
    ),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    service: UnifiedSearchService = Depends(get_search_service),
) -> SearchSuggestionResponse:
    """
    Get search suggestions based on partial query input.

    Useful for autocomplete functionality in search interfaces.
    """
    try:
        # For now, return basic suggestions from recent/popular searches
        # In a full implementation, this would use search analytics
        suggestions = [
            f"{query} genes",
            f"{query} variants",
            f"{query} phenotypes",
            f"{query} evidence",
        ][:limit]

        return SearchSuggestionResponse(
            query=query,
            suggestions=suggestions,
            total_suggestions=len(suggestions),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {e!s}",
        )


@router.get(
    "/stats",
    summary="Search statistics",
    response_model=SearchStatisticsResponse,
)
async def search_statistics(
    service: UnifiedSearchService = Depends(get_search_service),
) -> SearchStatisticsResponse:
    """
    Get statistics about searchable entities in the system.

    Useful for understanding the scope of available data.
    """
    try:
        # This would typically aggregate counts from all repositories
        # For now, return placeholder stats
        stats = {
            "total_entities": {
                "genes": 0,  # Would come from gene repository count
                "variants": 0,  # Would come from variant repository count
                "phenotypes": 0,  # Would come from phenotype repository count
                "evidence": 0,  # Would come from evidence repository count
            },
            "searchable_fields": {
                "genes": ["symbol", "name", "description"],
                "variants": ["variant_id", "gene_symbol", "clinical_significance"],
                "phenotypes": ["name", "hpo_id", "definition", "synonyms"],
                "evidence": ["description", "summary", "evidence_type"],
            },
            "last_updated": None,  # Would track when data was last indexed
        }

        return SearchStatisticsResponse(
            total_entities=cast("dict[str, int]", stats["total_entities"]),
            searchable_fields=cast("dict[str, list[str]]", stats["searchable_fields"]),
            last_updated=cast("str | None", stats["last_updated"]),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get search statistics: {e!s}",
        )
