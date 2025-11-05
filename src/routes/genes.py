"""
Gene API routes for MED13 Resource Library.

RESTful endpoints for gene management with CRUD operations.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.application.container import get_legacy_dependency_container
from src.routes.serializers import serialize_gene
from src.models.api import GeneResponse, GeneCreate, GeneUpdate, PaginatedResponse

if TYPE_CHECKING:
    from src.application.services.gene_service import GeneApplicationService

router = APIRouter(prefix="/genes", tags=["genes"])


def get_gene_service(db: Session = Depends(get_session)) -> "GeneApplicationService":
    """Dependency injection for gene application service."""
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_gene_application_service(db)


@router.get("/", summary="List genes", response_model=PaginatedResponse[GeneResponse])
async def get_genes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by gene symbol or name"),
    sort_by: str = Query("symbol", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> PaginatedResponse[GeneResponse]:
    """
    Retrieve a paginated list of genes.

    Supports searching by gene symbol or name, and sorting by various fields.
    """

    try:
        genes, total = service.list_genes(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )

        # Convert to response models
        gene_responses = [
            GeneResponse.model_validate(serialize_gene(gene)) for gene in genes
        ]

        total_pages = (total + per_page - 1) // per_page

        return PaginatedResponse(
            items=gene_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve genes: {str(e)}"
        )


@router.get("/{gene_id}", summary="Get gene by ID", response_model=GeneResponse)
async def get_gene(
    gene_id: str,
    include_variants: bool = Query(False, description="Include associated variants"),
    include_phenotypes: bool = Query(
        False, description="Include associated phenotypes"
    ),
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> GeneResponse:
    """
    Retrieve a specific gene by its identifier.

    Optionally include related variants and phenotypes in the response.
    """

    try:
        gene = service.get_gene_by_id(gene_id)
        if not gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        variant_summaries = (
            service.get_gene_variants(gene_id) if include_variants else None
        )
        phenotypes = (
            service.get_gene_phenotypes(gene_id) if include_phenotypes else None
        )

        serialized_gene = serialize_gene(
            gene,
            include_variants=include_variants,
            variants=variant_summaries,
            include_phenotypes=include_phenotypes,
            phenotypes=phenotypes,
        )

        return GeneResponse.model_validate(serialized_gene)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve gene: {str(e)}"
        )


@router.post(
    "/", summary="Create new gene", response_model=GeneResponse, status_code=201
)
async def create_gene(
    gene: GeneCreate,
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> GeneResponse:
    """
    Create a new gene record.

    The gene symbol will be automatically converted to uppercase.
    """

    try:
        # Check if gene already exists
        existing = service.get_gene_by_symbol(gene.symbol)
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Gene with symbol {gene.symbol} already exists"
            )

        created_gene = service.create_gene(
            symbol=gene.symbol,
            name=gene.name,
            description=gene.description,
            gene_type=gene.gene_type.value,
            chromosome=gene.chromosome,
            start_position=gene.start_position,
            end_position=gene.end_position,
            ensembl_id=gene.ensembl_id,
            ncbi_gene_id=gene.ncbi_gene_id,
            uniprot_id=gene.uniprot_id,
        )

        serialized = serialize_gene(created_gene)
        return GeneResponse.model_validate(serialized)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create gene: {str(e)}")


@router.put("/{gene_id}", summary="Update gene", response_model=GeneResponse)
async def update_gene(
    gene_id: str,
    gene_update: GeneUpdate,
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> GeneResponse:
    """
    Update an existing gene record.

    Only provided fields will be updated.
    """

    try:
        # Check if gene exists
        existing_gene = service.get_gene_by_id(gene_id)
        if not existing_gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        # Prepare update data
        update_data = gene_update.model_dump(exclude_unset=True)

        updated_gene = service.update_gene(gene_id, update_data)
        serialized = serialize_gene(updated_gene)
        return GeneResponse.model_validate(serialized)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update gene: {str(e)}")


@router.delete("/{gene_id}", summary="Delete gene", status_code=204)
async def delete_gene(
    gene_id: str,
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> None:
    """
    Delete a gene record.

    This operation cannot be undone.
    """

    try:
        # Check if gene exists
        existing_gene = service.get_gene_by_id(gene_id)
        if not existing_gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        # Check if gene has associated variants
        if service.gene_has_variants(gene_id):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete gene {gene_id}: associated variants exist",
            )

        service.delete_gene(gene_id)
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete gene: {str(e)}")


@router.get("/{gene_id}/statistics", summary="Get gene statistics")
async def get_gene_statistics(
    gene_id: str,
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> Dict[str, Any]:
    """
    Retrieve statistics for a specific gene.

    Includes variant counts, phenotype associations, and other metrics.
    """

    try:
        # Check if gene exists
        existing_gene = service.get_gene_by_id(gene_id)
        if not existing_gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        stats = service.get_gene_statistics(gene_id)
        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve gene statistics: {str(e)}"
        )
