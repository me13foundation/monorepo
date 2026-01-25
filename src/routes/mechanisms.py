"""
Mechanism API routes for MED13 Resource Library.

RESTful endpoints for mechanism management and mechanistic links.
"""

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.domain.value_objects.confidence import EvidenceLevel
from src.domain.value_objects.protein_structure import ProteinDomain
from src.infrastructure.dependency_injection.dependencies import (
    get_legacy_dependency_container,
)
from src.models.api import (
    MechanismCreate,
    MechanismResponse,
    MechanismUpdate,
    PaginatedResponse,
    ProteinDomainPayload,
)
from src.routes.serializers import serialize_mechanism
from src.type_definitions.common import MechanismUpdate as MechanismUpdatePayload

if TYPE_CHECKING:
    from src.application.services.mechanism_service import (
        MechanismApplicationService,
    )

router = APIRouter(prefix="/mechanisms", tags=["mechanisms"])


class MechanismListParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: str | None = Field(None, description="Search by name/description")
    sort_by: str = Field("name", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

    model_config = {"extra": "ignore"}


def get_mechanism_service(
    db: Session = Depends(get_session),
) -> "MechanismApplicationService":
    container = get_legacy_dependency_container()
    return container.create_mechanism_application_service(db)


def _payload_to_domains(
    payloads: list[ProteinDomainPayload],
) -> list[ProteinDomain]:
    return [ProteinDomain.model_validate(payload.model_dump()) for payload in payloads]


def _to_mechanism_update_payload(
    payload: MechanismUpdate,
) -> MechanismUpdatePayload:
    updates: MechanismUpdatePayload = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.evidence_tier is not None:
        updates["evidence_tier"] = payload.evidence_tier.value
    if payload.confidence_score is not None:
        updates["confidence_score"] = payload.confidence_score
    if payload.source is not None:
        updates["source"] = payload.source
    if payload.protein_domains is not None:
        updates["protein_domains"] = [
            domain.model_dump() for domain in payload.protein_domains
        ]
    if payload.phenotype_ids is not None:
        updates["phenotype_ids"] = payload.phenotype_ids
    return updates


@router.get(
    "/",
    summary="List mechanisms",
    response_model=PaginatedResponse[MechanismResponse],
)
async def list_mechanisms(
    params: MechanismListParams = Depends(),
    service: "MechanismApplicationService" = Depends(get_mechanism_service),
) -> PaginatedResponse[MechanismResponse]:
    """
    Retrieve a paginated list of mechanisms with optional search.
    """
    try:
        if params.search:
            mechanisms = service.search_mechanisms(
                params.search,
                limit=params.per_page,
                filters=None,
            )
            total = len(mechanisms)
            page = 1
        else:
            mechanisms, total = service.list_mechanisms(
                page=params.page,
                per_page=params.per_page,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                filters=None,
            )
            page = params.page

        responses = [serialize_mechanism(mech) for mech in mechanisms]
        total_pages = (total + params.per_page - 1) // params.per_page
        return PaginatedResponse(
            items=responses,
            total=total,
            page=page,
            per_page=params.per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve mechanisms: {e!s}",
        )


@router.get(
    "/{mechanism_id}",
    summary="Get mechanism by ID",
    response_model=MechanismResponse,
)
async def get_mechanism(
    mechanism_id: int,
    service: "MechanismApplicationService" = Depends(get_mechanism_service),
) -> MechanismResponse:
    """Retrieve a specific mechanism by its database ID."""
    try:
        mechanism = service.get_mechanism_by_id(mechanism_id)
        if not mechanism:
            raise HTTPException(
                status_code=404,
                detail=f"Mechanism {mechanism_id} not found",
            )
        return serialize_mechanism(mechanism)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve mechanism: {e!s}",
        )


@router.post(
    "/",
    summary="Create mechanism",
    response_model=MechanismResponse,
    status_code=201,
)
async def create_mechanism(
    payload: MechanismCreate,
    service: "MechanismApplicationService" = Depends(get_mechanism_service),
) -> MechanismResponse:
    """Create a new mechanism."""
    try:
        protein_domains = _payload_to_domains(payload.protein_domains)
        mechanism = service.create_mechanism(
            name=payload.name,
            description=payload.description,
            evidence_tier=EvidenceLevel(payload.evidence_tier.value),
            confidence_score=payload.confidence_score,
            source=payload.source,
            protein_domains=protein_domains,
            phenotype_ids=payload.phenotype_ids,
        )
        return serialize_mechanism(mechanism)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create mechanism: {e!s}",
        )


@router.put(
    "/{mechanism_id}",
    summary="Update mechanism",
    response_model=MechanismResponse,
)
async def update_mechanism(
    mechanism_id: int,
    payload: MechanismUpdate,
    service: "MechanismApplicationService" = Depends(get_mechanism_service),
) -> MechanismResponse:
    """Update an existing mechanism."""
    try:
        updates = _to_mechanism_update_payload(payload)
        mechanism = service.update_mechanism(mechanism_id, updates)
        return serialize_mechanism(mechanism)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update mechanism: {e!s}",
        )


@router.delete(
    "/{mechanism_id}",
    summary="Delete mechanism",
)
async def delete_mechanism(
    mechanism_id: int,
    service: "MechanismApplicationService" = Depends(get_mechanism_service),
) -> dict[str, str]:
    """Delete a mechanism by ID."""
    try:
        deleted = service.delete_mechanism(mechanism_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Mechanism {mechanism_id} not found",
            )
        return {"message": "Mechanism deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete mechanism: {e!s}",
        )


__all__ = ["router"]
