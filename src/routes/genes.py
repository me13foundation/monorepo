"""
Gene API routes for MED13 Resource Library.

RESTful endpoints for gene management with CRUD operations.
"""

from enum import Enum
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.dependency_injection.dependencies import (
    get_legacy_dependency_container,
)
from src.models.api import GeneCreate, GeneResponse, GeneUpdate, PaginatedResponse
from src.routes.serializers import serialize_gene
from src.type_definitions.common import GeneUpdate as GeneUpdatePayload
from src.type_definitions.common import JSONObject

if TYPE_CHECKING:
    from src.application.services.gene_service import GeneApplicationService

router = APIRouter(prefix="/genes", tags=["genes"])


def get_gene_service(db: Session = Depends(get_session)) -> "GeneApplicationService":
    """Dependency injection for gene application service."""
    # Get unified container with legacy support

    container = get_legacy_dependency_container()
    return container.create_gene_application_service(db)


def _enum_str(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _to_gene_update_payload(update: GeneUpdate) -> GeneUpdatePayload:
    payload: GeneUpdatePayload = {}
    if update.name is not None:
        payload["name"] = update.name
    if update.description is not None:
        payload["description"] = update.description
    if update.gene_type is not None:
        payload["gene_type"] = _enum_str(update.gene_type)
    if update.chromosome is not None:
        payload["chromosome"] = update.chromosome
    if update.start_position is not None:
        payload["start_position"] = update.start_position
    if update.end_position is not None:
        payload["end_position"] = update.end_position
    if update.ensembl_id is not None:
        payload["ensembl_id"] = update.ensembl_id
    if update.ncbi_gene_id is not None:
        payload["ncbi_gene_id"] = update.ncbi_gene_id
    if update.uniprot_id is not None:
        payload["uniprot_id"] = update.uniprot_id
    return payload


@router.get("/", summary="List genes", response_model=PaginatedResponse[GeneResponse])
async def get_genes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by gene symbol or name"),
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
        gene_responses = [serialize_gene(gene) for gene in genes]

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
            status_code=500,
            detail=f"Failed to retrieve genes: {e!s}",
        )


@router.get("/{gene_id}", summary="Get gene by ID", response_model=GeneResponse)
async def get_gene(
    gene_id: str,
    include_variants: bool = Query(False, description="Include associated variants"),
    include_phenotypes: bool = Query(
        False,
        description="Include associated phenotypes",
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

        return serialized_gene

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve gene: {e!s}",
        )


@router.post(
    "/",
    summary="Create new gene",
    response_model=GeneResponse,
    status_code=201,
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
                status_code=409,
                detail=f"Gene with symbol {gene.symbol} already exists",
            )

        created_gene = service.create_gene(
            {
                "symbol": gene.symbol,
                "name": gene.name,
                "description": gene.description,
                "gene_type": gene.gene_type.value,
                "chromosome": gene.chromosome,
                "start_position": gene.start_position,
                "end_position": gene.end_position,
                "ensembl_id": gene.ensembl_id,
                "ncbi_gene_id": gene.ncbi_gene_id,
                "uniprot_id": gene.uniprot_id,
            },
        )

        return serialize_gene(created_gene)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create gene: {e!s}")


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

        update_data = _to_gene_update_payload(gene_update)

        updated_gene = service.update_gene(gene_id, update_data)
        return serialize_gene(updated_gene)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update gene: {e!s}")


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
        return

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete gene: {e!s}")


@router.get(
    "/{gene_id}/statistics",
    summary="Get gene statistics",
    response_model=dict[str, int | float | bool | str | None],
)
async def get_gene_statistics(
    gene_id: str,
    service: "GeneApplicationService" = Depends(get_gene_service),
) -> JSONObject:
    """
    Retrieve statistics for a specific gene.

    Includes variant counts, phenotype associations, and other metrics.
    """

    try:
        # Check if gene exists
        existing_gene = service.get_gene_by_id(gene_id)
        if not existing_gene:
            raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")

        return service.get_gene_statistics(gene_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve gene statistics: {e!s}",
        )
