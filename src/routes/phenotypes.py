"""
Phenotype API routes for MED13 Resource Library.

RESTful endpoints for phenotype management with HPO ontology integration.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.dependency_injection import DependencyContainer
from src.routes.serializers import serialize_phenotype
from src.models.api import (
    PhenotypeResponse,
    PhenotypeCreate,
    PhenotypeUpdate,
    PaginatedResponse,
)

if TYPE_CHECKING:
    from src.application.services.phenotype_service import PhenotypeApplicationService

router = APIRouter(prefix="/phenotypes", tags=["phenotypes"])


def get_phenotype_service(
    db: Session = Depends(get_session),
) -> "PhenotypeApplicationService":
    """Dependency injection for phenotype application service."""
    container = DependencyContainer(db)
    return container.create_phenotype_application_service()


@router.get(
    "/", summary="List phenotypes", response_model=PaginatedResponse[PhenotypeResponse]
)
async def get_phenotypes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(
        None, description="Search by HPO term, name, or synonyms"
    ),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_root_term: Optional[bool] = Query(None, description="Filter by root terms"),
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> PaginatedResponse[PhenotypeResponse]:
    """
    Retrieve a paginated list of phenotypes with optional search and filters.
    """
    filters = {
        "category": category,
        "is_root_term": is_root_term,
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    try:
        phenotypes, total = service.list_phenotypes(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters,
        )

        phenotype_responses = [
            PhenotypeResponse.model_validate(serialize_phenotype(phenotype))
            for phenotype in phenotypes
        ]

        total_pages = (total + per_page - 1) // per_page
        return PaginatedResponse(
            items=phenotype_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve phenotypes: {str(e)}"
        )


@router.get(
    "/{phenotype_id}", summary="Get phenotype by ID", response_model=PhenotypeResponse
)
async def get_phenotype(
    phenotype_id: int,
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> PhenotypeResponse:
    """
    Retrieve a specific phenotype by its database ID.
    """
    try:
        # For now, we'll use get_by_id - may need to enhance service later
        phenotype = service.get_phenotype_by_hpo_id(
            f"HP:{phenotype_id:07d}"
        )  # Convert to HPO format
        if not phenotype:
            raise HTTPException(
                status_code=404, detail=f"Phenotype {phenotype_id} not found"
            )
        return PhenotypeResponse.model_validate(serialize_phenotype(phenotype))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve phenotype: {str(e)}"
        )


@router.get(
    "/hpo/{hpo_id}", summary="Get phenotype by HPO ID", response_model=PhenotypeResponse
)
async def get_phenotype_by_hpo_id(
    hpo_id: str,
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> PhenotypeResponse:
    """
    Retrieve a specific phenotype by its HPO identifier.
    """
    try:
        phenotype = service.get_phenotype_by_hpo_id(hpo_id)
        if not phenotype:
            raise HTTPException(
                status_code=404, detail=f"Phenotype with HPO ID {hpo_id} not found"
            )
        return PhenotypeResponse.model_validate(serialize_phenotype(phenotype))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve phenotype: {str(e)}"
        )


@router.post(
    "/",
    summary="Create new phenotype",
    response_model=PhenotypeResponse,
    status_code=201,
)
async def create_phenotype(
    phenotype_data: PhenotypeCreate,
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> PhenotypeResponse:
    """
    Create a new phenotype.
    """
    try:
        phenotype = service.create_phenotype(
            hpo_id=phenotype_data.hpo_id,
            name=phenotype_data.name,
            definition=phenotype_data.definition,
            category=phenotype_data.category,
            synonyms=phenotype_data.synonyms,
        )

        return PhenotypeResponse.model_validate(serialize_phenotype(phenotype))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create phenotype: {str(e)}"
        )


@router.put(
    "/{phenotype_id}", summary="Update phenotype", response_model=PhenotypeResponse
)
async def update_phenotype(
    phenotype_id: int,
    phenotype_data: PhenotypeUpdate,
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> PhenotypeResponse:
    """
    Update an existing phenotype by its database ID.
    """
    try:
        # Validate phenotype exists
        if not service.validate_phenotype_exists(phenotype_id):
            raise HTTPException(
                status_code=404, detail=f"Phenotype {phenotype_id} not found"
            )

        # Convert to dict for update
        updates = phenotype_data.model_dump(exclude_unset=True)

        phenotype = service.update_phenotype(phenotype_id, updates)
        return PhenotypeResponse.model_validate(serialize_phenotype(phenotype))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update phenotype: {str(e)}"
        )


@router.delete("/{phenotype_id}", summary="Delete phenotype", status_code=204)
async def delete_phenotype(
    phenotype_id: int,
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> None:
    """
    Delete a phenotype by its database ID.
    """
    try:
        if not service.validate_phenotype_exists(phenotype_id):
            raise HTTPException(
                status_code=404, detail=f"Phenotype {phenotype_id} not found"
            )

        # For now, implement soft delete or check dependencies
        # TODO: Implement proper deletion logic with dependency checks
        raise HTTPException(
            status_code=501,
            detail="Phenotype deletion not yet implemented - requires dependency analysis",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete phenotype: {str(e)}"
        )


@router.get("/search/", summary="Search phenotypes", response_model=Dict[str, Any])
async def search_phenotypes(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> Dict[str, Any]:
    """
    Search phenotypes by name, HPO term, or synonyms.
    """
    try:
        filters = {"category": category} if category else {}
        phenotypes = service.search_phenotypes(query, limit, filters)

        return {
            "query": query,
            "total_results": len(phenotypes),
            "results": [serialize_phenotype(p) for p in phenotypes],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search phenotypes: {str(e)}"
        )


@router.get("/category/{category}", summary="Get phenotypes by category")
async def get_phenotypes_by_category(
    category: str,
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Maximum number of results"
    ),
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> Dict[str, Any]:
    """
    Retrieve phenotypes filtered by clinical category.
    """
    try:
        phenotypes = service.get_phenotypes_by_category(category)

        if limit:
            phenotypes = phenotypes[:limit]

        return {
            "category": category,
            "total_results": len(phenotypes),
            "results": [serialize_phenotype(p) for p in phenotypes],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve phenotypes for category {category}: {str(e)}",
        )


@router.get(
    "/statistics/", summary="Get phenotype statistics", response_model=Dict[str, Any]
)
async def get_phenotype_statistics(
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> Dict[str, Any]:
    """
    Retrieve statistics about phenotypes in the repository.
    """
    try:
        stats = service.get_phenotype_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve phenotype statistics: {str(e)}"
        )


@router.get("/{phenotype_id}/evidence", summary="Get evidence for a phenotype")
async def get_phenotype_evidence(
    phenotype_id: int,
    service: "PhenotypeApplicationService" = Depends(get_phenotype_service),
) -> Dict[str, Any]:
    """
    Retrieve all evidence associated with a specific phenotype.
    """
    try:
        if not service.validate_phenotype_exists(phenotype_id):
            raise HTTPException(
                status_code=404, detail=f"Phenotype {phenotype_id} not found"
            )

        # TODO: Implement evidence retrieval for phenotypes
        return {
            "phenotype_id": phenotype_id,
            "evidence": [],
            "total_count": 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence for phenotype {phenotype_id}: {str(e)}",
        )
