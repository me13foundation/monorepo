"""
Gene API routes for MED13 Resource Library.

RESTful endpoints for gene management with CRUD operations.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.services.domain.gene_service import GeneService
from src.models.api import (
    GeneResponse,
    GeneCreate,
    GeneUpdate,
    PaginationParams,
    PaginatedResponse,
)

router = APIRouter(prefix="/genes", tags=["genes"])


@router.get("/", summary="List genes", response_model=PaginatedResponse[GeneResponse])
async def get_genes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by gene symbol or name"),
    sort_by: str = Query("symbol", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_session),
):
    """
    Retrieve a paginated list of genes.

    Supports searching by gene symbol or name, and sorting by various fields.
    """
    service = GeneService(db)

    # Build query parameters
    pagination = PaginationParams(
        page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order
    )

    try:
        if search:
            # Use search functionality
            genes = service.search_genes(search, pagination.page, pagination.per_page)
            total = service.count_search_results(search)
        else:
            # Get all genes with pagination
            genes = service.get_all_genes(pagination.page, pagination.per_page)
            total = service.count_all_genes()

        # Convert to response models
        gene_responses = [GeneResponse.model_validate(gene) for gene in genes]

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
    db: Session = Depends(get_session),
):
    """
    Retrieve a specific gene by its identifier.

    Optionally include related variants and phenotypes in the response.
    """
    service = GeneService(db)

    try:
        gene = service.get_gene_by_id(gene_id)
        if not gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        # Add computed fields
        gene_data = GeneResponse.model_validate(gene).model_dump()

        if include_variants:
            variants = service.get_gene_variants(gene_id)
            gene_data["variants"] = [v.model_dump() for v in variants]

        if include_phenotypes:
            phenotypes = service.get_gene_phenotypes(gene_id)
            gene_data["phenotypes"] = [p.model_dump() for p in phenotypes]

        return GeneResponse(**gene_data)

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
    db: Session = Depends(get_session),
):
    """
    Create a new gene record.

    The gene symbol will be automatically converted to uppercase.
    """
    service = GeneService(db)

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
            gene_type=gene.gene_type,
            chromosome=gene.chromosome,
            start_position=gene.start_position,
            end_position=gene.end_position,
            ensembl_id=gene.ensembl_id,
            ncbi_gene_id=gene.ncbi_gene_id,
            uniprot_id=gene.uniprot_id,
        )

        return GeneResponse.model_validate(created_gene)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create gene: {str(e)}")


@router.put("/{gene_id}", summary="Update gene", response_model=GeneResponse)
async def update_gene(
    gene_id: str,
    gene_update: GeneUpdate,
    db: Session = Depends(get_session),
):
    """
    Update an existing gene record.

    Only provided fields will be updated.
    """
    service = GeneService(db)

    try:
        # Check if gene exists
        existing_gene = service.get_gene_by_id(gene_id)
        if not existing_gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        # Prepare update data
        update_data = gene_update.model_dump(exclude_unset=True)

        updated_gene = service.update_gene(gene_id, update_data)
        return GeneResponse.model_validate(updated_gene)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update gene: {str(e)}")


@router.delete("/{gene_id}", summary="Delete gene", status_code=204)
async def delete_gene(
    gene_id: str,
    db: Session = Depends(get_session),
):
    """
    Delete a gene record.

    This operation cannot be undone.
    """
    service = GeneService(db)

    try:
        # Check if gene exists
        existing_gene = service.get_gene_by_id(gene_id)
        if not existing_gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        # Check if gene has associated variants
        if existing_gene.variants:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete gene {gene_id}: has {len(existing_gene.variants)} associated variants",
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
    db: Session = Depends(get_session),
):
    """
    Retrieve statistics for a specific gene.

    Includes variant counts, phenotype associations, and other metrics.
    """
    service = GeneService(db)

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
