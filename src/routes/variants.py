"""
Variant API routes for MED13 Resource Library.

RESTful endpoints for variant management with CRUD operations.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.dependency_injection import DependencyContainer
from src.routes.serializers import serialize_variant
from src.models.api import (
    VariantResponse,
    VariantCreate,
    VariantUpdate,
    PaginatedResponse,
)

if TYPE_CHECKING:
    from src.application.services.variant_service import VariantApplicationService

router = APIRouter(prefix="/variants", tags=["variants"])


def get_variant_service(
    db: Session = Depends(get_session),
) -> "VariantApplicationService":
    """Dependency injection for variant application service."""
    container = DependencyContainer(db)
    return container.create_variant_application_service()


@router.get(
    "/", summary="List variants", response_model=PaginatedResponse[VariantResponse]
)
async def get_variants(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by variant ID or HGVS"),
    sort_by: str = Query("variant_id", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    gene_id: Optional[str] = Query(None, description="Filter by gene ID"),
    clinical_significance: Optional[str] = Query(
        None, description="Filter by clinical significance"
    ),
    variant_type: Optional[str] = Query(None, description="Filter by variant type"),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> PaginatedResponse[VariantResponse]:
    """
    Retrieve a paginated list of variants.

    Supports filtering by gene, clinical significance, and variant type.
    """

    try:
        # Build filters dictionary
        filters = {}
        if gene_id:
            filters["gene_id"] = gene_id
        if clinical_significance:
            filters["clinical_significance"] = clinical_significance
        if variant_type:
            filters["variant_type"] = variant_type

        variants, total = service.list_variants(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters,
        )

        variant_responses = [
            VariantResponse.model_validate(serialize_variant(variant))
            for variant in variants
        ]

        total_pages = (total + per_page - 1) // per_page
        return PaginatedResponse(
            items=variant_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve variants: {str(e)}"
        )


@router.get(
    "/{variant_id}", summary="Get variant by ID", response_model=VariantResponse
)
async def get_variant(
    variant_id: str,
    include_evidence: bool = Query(False, description="Include associated evidence"),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    """
    Retrieve a specific variant by its ID.

    Optionally includes associated evidence records.
    """

    try:
        if include_evidence:
            variant = service.get_variant_with_evidence(int(variant_id))
        else:
            variant = service.get_variant_by_id(variant_id)

        if variant is None:
            raise HTTPException(
                status_code=404, detail=f"Variant {variant_id} not found"
            )

        return VariantResponse.model_validate(serialize_variant(variant))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve variant: {str(e)}"
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
    """
    Retrieve a variant by its ClinVar accession ID.
    """

    try:
        variant = service.get_variant_by_clinvar_id(clinvar_id)
        if variant is None:
            raise HTTPException(
                status_code=404,
                detail=f"Variant with ClinVar ID {clinvar_id} not found",
            )

        return VariantResponse.model_validate(serialize_variant(variant))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve variant: {str(e)}"
        )


@router.post(
    "/", summary="Create variant", response_model=VariantResponse, status_code=201
)
async def create_variant(
    variant_data: VariantCreate,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    """
    Create a new variant.
    """

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
                variant_data, "clinical_significance", "not_provided"
            ),
            hgvs_genomic=getattr(variant_data, "hgvs_genomic", None),
            hgvs_protein=getattr(variant_data, "hgvs_protein", None),
            hgvs_cdna=getattr(variant_data, "hgvs_cdna", None),
            condition=getattr(variant_data, "condition", None),
            review_status=getattr(variant_data, "review_status", None),
            allele_frequency=getattr(variant_data, "allele_frequency", None),
            gnomad_af=getattr(variant_data, "gnomad_af", None),
        )

        return VariantResponse.model_validate(serialize_variant(variant))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create variant: {str(e)}"
        )


@router.put("/{variant_id}", summary="Update variant", response_model=VariantResponse)
async def update_variant(
    variant_id: int,
    variant_data: VariantUpdate,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    """
    Update an existing variant.
    """

    try:
        # Validate variant exists
        if not service.validate_variant_exists(variant_id):
            raise HTTPException(
                status_code=404, detail=f"Variant {variant_id} not found"
            )

        # Convert to dict for update
        updates = variant_data.model_dump(exclude_unset=True)

        variant = service.update_variant(variant_id, updates)
        return VariantResponse.model_validate(serialize_variant(variant))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update variant: {str(e)}"
        )


@router.put(
    "/{variant_id}/classification",
    summary="Update variant classification",
    response_model=VariantResponse,
)
async def update_variant_classification(
    variant_id: int,
    variant_type: Optional[str] = Query(None, description="New variant type"),
    clinical_significance: Optional[str] = Query(
        None, description="New clinical significance"
    ),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> VariantResponse:
    """
    Update variant classification information.
    """

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

        return VariantResponse.model_validate(serialize_variant(variant))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update variant classification: {str(e)}"
        )


@router.get("/{variant_id}/evidence", summary="Get variant evidence")
async def get_variant_evidence(
    variant_id: int,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> Dict[str, Any]:
    """
    Get evidence associated with a variant.
    """

    try:
        if not service.validate_variant_exists(variant_id):
            raise HTTPException(
                status_code=404, detail=f"Variant {variant_id} not found"
            )

        # Get evidence conflicts and confidence score
        conflicts = service.detect_evidence_conflicts(variant_id)
        confidence = service.assess_clinical_significance_confidence(variant_id)

        return {
            "variant_id": variant_id,
            "evidence_conflicts": conflicts,
            "clinical_significance_confidence": confidence,
            "conflict_count": len(conflicts),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve variant evidence: {str(e)}"
        )


@router.get("/gene/{gene_id}", summary="Get variants by gene")
async def get_variants_by_gene(
    gene_id: int,
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Maximum number of results"
    ),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> Dict[str, Any]:
    """
    Retrieve variants associated with a specific gene.
    """

    try:
        variants = service.get_variants_by_gene(gene_id, limit)
        serialized_variants = [serialize_variant(variant) for variant in variants]

        return {
            "gene_id": gene_id,
            "variants": serialized_variants,
            "count": len(serialized_variants),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve variants for gene: {str(e)}"
        )


@router.get("/search", summary="Search variants")
async def search_variants(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    gene_id: Optional[str] = Query(None, description="Filter by gene ID"),
    clinical_significance: Optional[str] = Query(
        None, description="Filter by clinical significance"
    ),
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> Dict[str, Any]:
    """
    Search variants by query with optional filters.
    """

    try:
        # Build filters
        filters = {}
        if gene_id:
            filters["gene_id"] = gene_id
        if clinical_significance:
            filters["clinical_significance"] = clinical_significance

        variants = service.search_variants(q, limit, filters)
        serialized_variants = [serialize_variant(variant) for variant in variants]

        return {
            "query": q,
            "results": serialized_variants,
            "count": len(serialized_variants),
            "filters": filters,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search variants: {str(e)}"
        )


@router.delete("/{variant_id}", summary="Delete variant", status_code=204)
async def delete_variant(
    variant_id: int,
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> None:
    """
    Delete a variant by ID.

    Note: This operation may be restricted based on data integrity rules.
    """

    try:
        if not service.validate_variant_exists(variant_id):
            raise HTTPException(
                status_code=404, detail=f"Variant {variant_id} not found"
            )

        # For now, we'll implement soft delete or check for dependencies
        # In a real implementation, you might want to check for associated evidence
        # and either prevent deletion or cascade

        # TODO: Implement proper deletion logic with dependency checks
        raise HTTPException(
            status_code=501,
            detail="Variant deletion not yet implemented - requires dependency analysis",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete variant: {str(e)}"
        )


@router.get("/stats", summary="Get variant statistics")
async def get_variant_statistics(
    service: "VariantApplicationService" = Depends(get_variant_service),
) -> Dict[str, Any]:
    """
    Retrieve statistical information about variants in the database.
    """

    try:
        stats = service.get_variant_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve statistics: {str(e)}"
        )
