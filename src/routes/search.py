"""
Unified Search API routes for MED13 Resource Library.

Provides cross-entity search capabilities with relevance scoring.
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.container import get_legacy_dependency_container
from src.application.search.search_service import SearchEntity
from src.database.session import get_session

if TYPE_CHECKING:
    from src.application.search.search_service import UnifiedSearchService

router = APIRouter(prefix="/search", tags=["search"])


def get_search_service(db: Session = Depends(get_session)) -> "UnifiedSearchService":
    """Dependency injection for unified search service."""
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_unified_search_service(db)


@router.post("/", summary="Unified search across all entities")
async def unified_search(
    query: str = Query(..., min_length=1, max_length=200, description="Search query"),
    entity_types: list[SearchEntity]
    | None = Query(
        None,
        description="Entity types to search (defaults to all)",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results per entity type"),
    service: "UnifiedSearchService" = Depends(get_search_service),
) -> dict[str, Any]:
    """
    Perform unified search across genes, variants, phenotypes, and evidence.

    Returns results sorted by relevance score with metadata for each entity type.
    """
    try:
        results = service.search(
            query=query,
            entity_types=entity_types,
            limit=limit,
        )

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}")


@router.get("/suggest", summary="Search suggestions")
async def search_suggestions(
    query: str = Query(
        ...,
        min_length=1,
        max_length=50,
        description="Partial search query",
    ),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    service: "UnifiedSearchService" = Depends(get_search_service),
) -> dict[str, Any]:
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

        return {
            "query": query,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {e!s}",
        )


@router.get("/stats", summary="Search statistics")
async def search_statistics(
    service: "UnifiedSearchService" = Depends(get_search_service),
) -> dict[str, Any]:
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

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get search statistics: {e!s}",
        )
