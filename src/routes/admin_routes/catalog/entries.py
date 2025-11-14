"""Endpoints for catalog entry listing."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.session import get_session
from src.infrastructure.repositories.data_discovery_repository_impl import (
    SQLAlchemySourceCatalogRepository,
)

from .mappers import catalog_entry_to_response
from .schemas import CatalogEntryResponse

router = APIRouter()


@router.get(
    "/",
    response_model=list[CatalogEntryResponse],
    summary="List source catalog entries",
    description="Retrieve the global data catalog entries.",
)
def list_catalog_entries(
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search query"),
    session: Session = Depends(get_session),
) -> list[CatalogEntryResponse]:
    """List catalog entries with optional filtering."""
    repo = SQLAlchemySourceCatalogRepository(session)
    if search:
        entries = repo.search(search, category)
    elif category:
        entries = repo.find_by_category(category)
    else:
        entries = repo.find_all()
    return [catalog_entry_to_response(entry) for entry in entries]


__all__ = ["router"]
