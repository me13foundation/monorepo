"""Variant API routes for MED13 Resource Library."""

from enum import Enum
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.dependency_injection.dependencies import (
    get_legacy_dependency_container,
)
from src.models.api import (
    PaginatedResponse,
    VariantCreate,
    VariantResponse,
    VariantUpdate,
)
from src.routes.serializers import serialize_variant
from src.type_definitions.common import JSONObject, QueryFilters
from src.type_definitions.common import VariantUpdate as VariantUpdatePayload

if TYPE_CHECKING:
    from src.application.services.variant_service import VariantApplicationService

router = APIRouter(prefix="/variants", tags=["variants"])


def get_variant_service(
    db: Session = Depends(get_session),
) -> "VariantApplicationService":
    """Dependency injection for variant application service."""
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_variant_application_service(db)


class VariantEvidenceSummaryResponse(BaseModel):
    """Response summarizing evidence associated with a variant."""

    variant_id: int
    evidence_conflicts: list[str]
    clinical_significance_confidence: float
    conflict_count: int


class VariantsByGeneResponse(BaseModel):
    """Response for variants associated with a gene."""

    gene_id: int
    variants: list[VariantResponse]
    count: int


class VariantSearchResponse(BaseModel):
    """Response payload for variant search operations."""

    query: str
    results: list[VariantResponse]
    count: int
    filters: QueryFilters | None


class VariantListParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: str | None = Field(None, description="Search by variant ID or HGVS")
    sort_by: str = Field("variant_id", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")
    gene_id: str | None = Field(None, description="Filter by gene ID")
    clinical_significance: str | None = Field(
        None,
        description="Filter by clinical significance",
    )
    variant_type: str | None = Field(None, description="Filter by variant type")

    model_config = {"extra": "ignore"}


@router.get(
    "/",
    summary="List variants",
    response_model=PaginatedResponse[VariantResponse],
)
async def get_variants(
    params: VariantListParams = Depends(),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> PaginatedResponse[VariantResponse]:
    try:
        # Build filters dictionary
        filters_payload: QueryFilters = {}
        if params.gene_id:
            filters_payload["gene_id"] = params.gene_id
        if params.clinical_significance:
            filters_payload["clinical_significance"] = params.clinical_significance
        if params.variant_type:
            filters_payload["variant_type"] = params.variant_type

        filters_arg = filters_payload or None

        variants, total = service.list_variants(
            page=params.page,
            per_page=params.per_page,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            filters=filters_arg,
        )

        variant_responses = [serialize_variant(variant) for variant in variants]

        total_pages = (total + params.per_page - 1) // params.per_page
        return PaginatedResponse(
            items=variant_responses,
            total=total,
            page=params.page,
            per_page=params.per_page,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve variants: {e!s}",
        )


@router.get(
    "/{variant_id}",
    summary="Get variant by ID",
    response_model=VariantResponse,
)
async def get_variant(
    variant_id: str,
    include_evidence: bool = Query(False, description="Include associated evidence"),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    try:
        if include_evidence:
            variant = service.get_variant_with_evidence(int(variant_id))
        else:
            variant = service.get_variant_by_id(variant_id)

        if variant is None:
            raise HTTPException(
                status_code=404,
                detail=f"Variant {variant_id} not found",
            )

        return serialize_variant(variant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve variant: {e!s}",
        )


@router.get(
    "/clinvar/{clinvar_id}",
    summary="Get variant by ClinVar ID",
    response_model=VariantResponse,
)
async def get_variant_by_clinvar_id(
    clinvar_id: str,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    try:
        variant = service.get_variant_by_clinvar_id(clinvar_id)
        if variant is None:
            raise HTTPException(
                status_code=404,
                detail=f"Variant with ClinVar ID {clinvar_id} not found",
            )

        return serialize_variant(variant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve variant: {e!s}",
        )


@router.post(
    "/",
    summary="Create variant",
    response_model=VariantResponse,
    status_code=201,
)
async def create_variant(
    variant_data: VariantCreate,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    try:
        variant = service.create_variant(
            chromosome=variant_data.chromosome,
            position=variant_data.position,
            reference_allele=variant_data.reference_allele,
            alternate_allele=variant_data.alternate_allele,
            variant_id=getattr(variant_data, "variant_id", None),
            clinvar_id=getattr(variant_data, "clinvar_id", None),
            variant_type=getattr(variant_data, "variant_type", "unknown"),
            clinical_significance=getattr(
                variant_data,
                "clinical_significance",
                "not_provided",
            ),
            hgvs_genomic=getattr(variant_data, "hgvs_genomic", None),
            hgvs_protein=getattr(variant_data, "hgvs_protein", None),
            hgvs_cdna=getattr(variant_data, "hgvs_cdna", None),
            condition=getattr(variant_data, "condition", None),
            review_status=getattr(variant_data, "review_status", None),
            allele_frequency=getattr(variant_data, "allele_frequency", None),
            gnomad_af=getattr(variant_data, "gnomad_af", None),
        )

        return serialize_variant(variant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create variant: {e!s}",
        )


@router.put("/{variant_id}", summary="Update variant", response_model=VariantResponse)
async def update_variant(
    variant_id: int,
    variant_data: VariantUpdate,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    try:
        # Validate variant exists
        if not service.validate_variant_exists(variant_id):
            raise HTTPException(
                status_code=404,
                detail=f"Variant {variant_id} not found",
            )

        updates = _to_variant_update_payload(variant_data)

        variant = service.update_variant(variant_id, updates)
        return serialize_variant(variant)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update variant: {e!s}",
        )


@router.put(
    "/{variant_id}/classification",
    summary="Update variant classification",
    response_model=VariantResponse,
)
async def update_variant_classification(
    variant_id: int,
    variant_type: str | None = Query(None, description="New variant type"),
    clinical_significance: str | None = Query(
        None,
        description="New clinical significance",
    ),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    try:
        if variant_type is None and clinical_significance is None:
            raise HTTPException(
                status_code=400,
                detail="At least one of variant_type or clinical_significance must be provided",
            )

        variant = service.update_variant_classification(
            variant_id=variant_id,
            variant_type=variant_type,
            clinical_significance=clinical_significance,
        )

        return serialize_variant(variant)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update variant classification: {e!s}",
        )


@router.get(
    "/{variant_id}/evidence",
    summary="Get variant evidence",
    response_model=VariantEvidenceSummaryResponse,
)
async def get_variant_evidence(
    variant_id: int,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantEvidenceSummaryResponse:
    try:
        if not service.validate_variant_exists(variant_id):
            raise HTTPException(
                status_code=404,
                detail=f"Variant {variant_id} not found",
            )

        # Get evidence conflicts and confidence score
        conflicts = service.detect_evidence_conflicts(variant_id)
        confidence = service.assess_clinical_significance_confidence(variant_id)

        return VariantEvidenceSummaryResponse(
            variant_id=variant_id,
            evidence_conflicts=conflicts,
            clinical_significance_confidence=confidence,
            conflict_count=len(conflicts),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve variant evidence: {e!s}",
        )


@router.get(
    "/gene/{gene_id}",
    summary="Get variants by gene",
    response_model=VariantsByGeneResponse,
)
async def get_variants_by_gene(
    gene_id: int,
    limit: int | None = Query(
        None,
        ge=1,
        le=100,
        description="Maximum number of results",
    ),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantsByGeneResponse:
    try:
        variants = service.get_variants_by_gene(gene_id, limit)
        serialized_variants = [serialize_variant(variant) for variant in variants]

        return VariantsByGeneResponse(
            gene_id=gene_id,
            variants=serialized_variants,
            count=len(serialized_variants),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve variants for gene: {e!s}",
        )


@router.get(
    "/search",
    summary="Search variants",
    response_model=VariantSearchResponse,
)
async def search_variants(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    gene_id: str | None = Query(None, description="Filter by gene ID"),
    clinical_significance: str | None = Query(
        None,
        description="Filter by clinical significance",
    ),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantSearchResponse:
    try:
        # Build filters
        filters_payload: QueryFilters = {}
        if gene_id:
            filters_payload["gene_id"] = gene_id
        if clinical_significance:
            filters_payload["clinical_significance"] = clinical_significance

        filters_arg = filters_payload or None

        variants = service.search_variants(q, limit, filters_arg)
        serialized_variants = [serialize_variant(variant) for variant in variants]

        return VariantSearchResponse(
            query=q,
            results=serialized_variants,
            count=len(serialized_variants),
            filters=filters_arg,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search variants: {e!s}",
        )


@router.delete("/{variant_id}", summary="Delete variant", status_code=204)
async def delete_variant(
    variant_id: int,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> None:
    """Delete a variant placeholder (currently not implemented)."""
    if not service.validate_variant_exists(variant_id):
        raise HTTPException(
            status_code=404,
            detail=f"Variant {variant_id} not found",
        )

    # TODO: Implement proper deletion logic with dependency checks
    raise HTTPException(
        status_code=501,
        detail="Variant deletion not yet implemented - requires dependency analysis",
    )


@router.get(
    "/stats",
    summary="Get variant statistics",
    response_model=dict[str, int | float | bool | str | None],
)
async def get_variant_statistics(
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> JSONObject:
    return service.get_variant_statistics()


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _to_variant_update_payload(variant_data: VariantUpdate) -> VariantUpdatePayload:
    """Convert the Pydantic variant update into a typed payload."""
    updates: VariantUpdatePayload = {}

    if variant_data.clinvar_id is not None:
        updates["clinvar_id"] = variant_data.clinvar_id
    if variant_data.hgvs_genomic is not None:
        updates["hgvs_genomic"] = variant_data.hgvs_genomic
    if variant_data.hgvs_protein is not None:
        updates["hgvs_protein"] = variant_data.hgvs_protein
    if variant_data.hgvs_cdna is not None:
        updates["hgvs_cdna"] = variant_data.hgvs_cdna
    if variant_data.variant_type is not None:
        updates["variant_type"] = _enum_value(variant_data.variant_type)
    if variant_data.clinical_significance is not None:
        updates["clinical_significance"] = _enum_value(
            variant_data.clinical_significance,
        )
    if variant_data.condition is not None:
        updates["condition"] = variant_data.condition
    if variant_data.review_status is not None:
        updates["review_status"] = variant_data.review_status
    if variant_data.allele_frequency is not None:
        updates["allele_frequency"] = variant_data.allele_frequency
    if variant_data.gnomad_af is not None:
        updates["gnomad_af"] = variant_data.gnomad_af

    return updates
