"""
Evidence API routes for MED13 Resource Library.

RESTful endpoints for evidence management linking variants and phenotypes.
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.container import get_legacy_dependency_container
from src.database.session import get_session
from src.domain.value_objects.confidence import EvidenceLevel
from src.models.api import (
    EvidenceCreate,
    EvidenceResponse,
    EvidenceUpdate,
    PaginatedResponse,
)
from src.routes.serializers import serialize_evidence

if TYPE_CHECKING:
    from src.application.services.evidence_service import EvidenceApplicationService

router = APIRouter(prefix="/evidence", tags=["evidence"])


def get_evidence_service(
    db: Session = Depends(get_session),
) -> "EvidenceApplicationService":
    """Dependency injection for evidence application service."""
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_evidence_application_service(db)


@router.get(
    "/",
    summary="List evidence",
    response_model=PaginatedResponse[EvidenceResponse],
)
async def get_evidence(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search in description or summary"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    variant_id: str | None = Query(None, description="Filter by variant ID"),
    phenotype_id: str | None = Query(None, description="Filter by phenotype ID"),
    evidence_level: str | None = Query(None, description="Filter by evidence level"),
    evidence_type: str | None = Query(None, description="Filter by evidence type"),
    reviewed: bool | None = Query(None, description="Filter by review status"),
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> PaginatedResponse[EvidenceResponse]:
    """
    Retrieve a paginated list of evidence records with optional search and filters.
    """
    filters = {
        "variant_id": variant_id,
        "phenotype_id": phenotype_id,
        "evidence_level": evidence_level,
        "evidence_type": evidence_type,
        "reviewed": reviewed,
    }
    filters = {k: v for k, v in filters.items() if v is not None}

    try:
        evidence_list, total = service.list_evidence(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters,
        )

        evidence_responses = [
            EvidenceResponse.model_validate(serialize_evidence(evidence))
            for evidence in evidence_list
        ]

        total_pages = (total + per_page - 1) // per_page
        return PaginatedResponse(
            items=evidence_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence: {e!s}",
        )


@router.get(
    "/{evidence_id}",
    summary="Get evidence by ID",
    response_model=EvidenceResponse,
)
async def get_evidence_by_id(
    evidence_id: int,
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> EvidenceResponse:
    """
    Retrieve a specific evidence record by its database ID.
    """
    try:
        # For now, we'll use get_by_id - may need to enhance service later
        evidence = service._evidence_repository.get_by_id(
            evidence_id,
        )  # Direct access for now
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence {evidence_id} not found",
            )
        return EvidenceResponse.model_validate(serialize_evidence(evidence))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence: {e!s}",
        )


@router.post(
    "/",
    summary="Create new evidence",
    response_model=EvidenceResponse,
    status_code=201,
)
async def create_evidence(
    evidence_data: EvidenceCreate,
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> EvidenceResponse:
    """
    Create a new evidence record linking a variant and phenotype.
    """
    try:
        evidence = service.create_evidence(
            variant_id=int(evidence_data.variant_id),
            phenotype_id=int(evidence_data.phenotype_id),
            description=evidence_data.description,
            summary=evidence_data.summary,
            evidence_level=EvidenceLevel(evidence_data.evidence_level.value),
            evidence_type=evidence_data.evidence_type,
            publication_id=(
                int(evidence_data.publication_id)
                if evidence_data.publication_id
                else None
            ),
            confidence_score=evidence_data.confidence_score,
            quality_score=evidence_data.quality_score,
            sample_size=evidence_data.sample_size,
            study_type=evidence_data.study_type,
            statistical_significance=evidence_data.statistical_significance,
            reviewed=evidence_data.reviewed,
            review_date=evidence_data.review_date,
            reviewer_notes=evidence_data.reviewer_notes,
        )

        return EvidenceResponse.model_validate(serialize_evidence(evidence))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create evidence: {e!s}",
        )


@router.put(
    "/{evidence_id}",
    summary="Update evidence",
    response_model=EvidenceResponse,
)
async def update_evidence(
    evidence_id: int,
    evidence_data: EvidenceUpdate,
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> EvidenceResponse:
    """
    Update an existing evidence record by its database ID.
    """
    try:
        # Validate evidence exists
        if not service.validate_evidence_exists(evidence_id):
            raise HTTPException(
                status_code=404,
                detail=f"Evidence {evidence_id} not found",
            )

        # Convert to dict for update
        updates = evidence_data.model_dump(exclude_unset=True)

        evidence = service.update_evidence(evidence_id, updates)
        return EvidenceResponse.model_validate(serialize_evidence(evidence))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update evidence: {e!s}",
        )


@router.delete("/{evidence_id}", summary="Delete evidence", status_code=204)
async def delete_evidence(
    evidence_id: int,
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> None:
    """
    Delete an evidence record by its database ID.
    """
    try:
        if not service.validate_evidence_exists(evidence_id):
            raise HTTPException(
                status_code=404,
                detail=f"Evidence {evidence_id} not found",
            )

        # For now, implement soft delete or check dependencies
        # TODO: Implement proper deletion logic with dependency checks
        raise HTTPException(
            status_code=501,
            detail="Evidence deletion not yet implemented - requires dependency analysis",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete evidence: {e!s}",
        )


@router.get("/variant/{variant_id}", summary="Get evidence for a variant")
async def get_evidence_by_variant(
    variant_id: int,
    limit: int
    | None = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of results",
    ),
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> dict[str, Any]:
    """
    Retrieve all evidence associated with a specific variant.
    """
    try:
        evidence_list = service.get_evidence_by_variant(variant_id)

        if limit:
            evidence_list = evidence_list[:limit]

        return {
            "variant_id": variant_id,
            "total_count": len(evidence_list),
            "evidence": [serialize_evidence(ev) for ev in evidence_list],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence for variant {variant_id}: {e!s}",
        )


@router.get("/phenotype/{phenotype_id}", summary="Get evidence for a phenotype")
async def get_evidence_by_phenotype(
    phenotype_id: int,
    limit: int
    | None = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of results",
    ),
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> dict[str, Any]:
    """
    Retrieve all evidence associated with a specific phenotype.
    """
    try:
        evidence_list = service.get_evidence_by_phenotype(phenotype_id)

        if limit:
            evidence_list = evidence_list[:limit]

        return {
            "phenotype_id": phenotype_id,
            "total_count": len(evidence_list),
            "evidence": [serialize_evidence(ev) for ev in evidence_list],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence for phenotype {phenotype_id}: {e!s}",
        )


@router.get("/search/", summary="Search evidence", response_model=dict[str, Any])
async def search_evidence(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    variant_id: str | None = Query(None, description="Filter by variant ID"),
    phenotype_id: str | None = Query(None, description="Filter by phenotype ID"),
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> dict[str, Any]:
    """
    Search evidence records by description, summary, or other text fields.
    """
    try:
        filters = {
            "variant_id": variant_id,
            "phenotype_id": phenotype_id,
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        evidence_list = service.search_evidence(query, limit, filters)

        return {
            "query": query,
            "total_results": len(evidence_list),
            "results": [serialize_evidence(ev) for ev in evidence_list],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search evidence: {e!s}",
        )


@router.get("/variant/{variant_id}/conflicts", summary="Detect conflicts for a variant")
async def get_evidence_conflicts(
    variant_id: int,
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> dict[str, Any]:
    """
    Detect and list any conflicting evidence records for a given variant.
    """
    try:
        conflicts = service.detect_evidence_conflicts(variant_id)
        return {
            "variant_id": variant_id,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect conflicts for variant {variant_id}: {e!s}",
        )


@router.get(
    "/variant/{variant_id}/consensus",
    summary="Get evidence consensus for a variant",
)
async def get_evidence_consensus(
    variant_id: int,
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> dict[str, Any]:
    """
    Calculate consensus from multiple evidence records for a variant.
    """
    try:
        consensus = service.calculate_evidence_consensus(variant_id)
        return {
            "variant_id": variant_id,
            "consensus": consensus,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate consensus for variant {variant_id}: {e!s}",
        )


@router.get(
    "/statistics/",
    summary="Get evidence statistics",
    response_model=dict[str, Any],
)
async def get_evidence_statistics(
    service: "EvidenceApplicationService" = Depends(get_evidence_service),
) -> dict[str, Any]:
    """
    Retrieve statistics about evidence in the repository.
    """
    try:
        stats = service.get_evidence_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence statistics: {e!s}",
        )
