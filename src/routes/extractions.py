"""
Publication extraction API routes.

Read-only endpoints for extracted publication facts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.domain.repositories.base import QuerySpecification
from src.domain.services.storage_providers.errors import StorageOperationError
from src.infrastructure.dependency_injection.dependencies import (
    get_legacy_dependency_container,
)
from src.models.api import (
    PaginatedResponse,
    PublicationExtractionDocumentResponse,
    PublicationExtractionResponse,
)
from src.routes.serializers import serialize_publication_extraction
from src.type_definitions.common import QueryFilters
from src.type_definitions.storage import StorageUseCase

if TYPE_CHECKING:
    from src.application.services.publication_extraction_service import (
        PublicationExtractionService,
    )
    from src.application.services.storage_configuration_service import (
        StorageConfigurationService,
    )


class ExtractionListParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("extracted_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    publication_id: int | None = Field(None, description="Filter by publication id")
    source_id: UUID | None = Field(None, description="Filter by source id")
    ingestion_job_id: UUID | None = Field(
        None,
        description="Filter by ingestion job id",
    )
    status: str | None = Field(None, description="Filter by extraction status")

    model_config = {"extra": "ignore"}


router = APIRouter(prefix="/extractions", tags=["extractions"])


def get_extraction_service(
    db: Session = Depends(get_session),
) -> PublicationExtractionService:
    container = get_legacy_dependency_container()
    return container.create_publication_extraction_service(db)


def get_storage_configuration_service(
    db: Session = Depends(get_session),
) -> StorageConfigurationService:
    container = get_legacy_dependency_container()
    return container.create_storage_configuration_service(db)


@router.get(
    "/",
    summary="List publication extractions",
    response_model=PaginatedResponse[PublicationExtractionResponse],
)
async def list_extractions(
    params: ExtractionListParams = Depends(),
    service: PublicationExtractionService = Depends(get_extraction_service),
) -> PaginatedResponse[PublicationExtractionResponse]:
    filters: QueryFilters = {}
    if params.publication_id is not None:
        filters["publication_id"] = params.publication_id
    if params.source_id is not None:
        filters["source_id"] = str(params.source_id)
    if params.ingestion_job_id is not None:
        filters["ingestion_job_id"] = str(params.ingestion_job_id)
    if params.status is not None:
        filters["status"] = params.status

    offset = max(params.page - 1, 0) * params.per_page
    spec = QuerySpecification(
        filters=filters,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        limit=params.per_page,
        offset=offset,
    )
    result = service.list_extractions(spec)
    items = [serialize_publication_extraction(item) for item in result.items]
    total_pages = (
        (result.total + params.per_page - 1) // params.per_page
        if params.per_page > 0
        else 1
    )
    return PaginatedResponse[PublicationExtractionResponse](
        items=items,
        total=result.total,
        page=params.page,
        per_page=params.per_page,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )


@router.get(
    "/{extraction_id}",
    summary="Get extraction by ID",
    response_model=PublicationExtractionResponse,
)
async def get_extraction(
    extraction_id: UUID,
    service: PublicationExtractionService = Depends(get_extraction_service),
) -> PublicationExtractionResponse:
    extraction = service.get_by_id(extraction_id)
    if extraction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction {extraction_id} not found",
        )
    return serialize_publication_extraction(extraction)


@router.get(
    "/{extraction_id}/document-url",
    summary="Get extraction document URL",
    response_model=PublicationExtractionDocumentResponse,
)
async def get_extraction_document_url(
    extraction_id: UUID,
    service: PublicationExtractionService = Depends(get_extraction_service),
    storage_service: StorageConfigurationService = Depends(
        get_storage_configuration_service,
    ),
) -> PublicationExtractionDocumentResponse:
    extraction = service.get_by_id(extraction_id)
    if extraction is None:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction {extraction_id} not found",
        )
    if not extraction.document_reference:
        raise HTTPException(
            status_code=404,
            detail=f"Extraction {extraction_id} has no stored document reference",
        )
    try:
        url = await storage_service.get_file_url_for_use_case(
            StorageUseCase.RAW_SOURCE,
            key=extraction.document_reference,
            user_id=None,
            metadata={"extraction_id": str(extraction.id)},
        )
    except StorageOperationError as exc:
        reason = None
        if exc.details is not None and isinstance(exc.details.get("reason"), str):
            reason = exc.details["reason"]
        status_code = 404 if reason == "missing" else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return PublicationExtractionDocumentResponse(
        extraction_id=str(extraction.id),
        document_reference=extraction.document_reference,
        url=url,
    )
