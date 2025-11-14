"""Router aggregation for admin data source endpoints."""

from fastapi import APIRouter

from .crud import router as crud_router
from .listing import router as listing_router

router = APIRouter()

router.include_router(listing_router, prefix="/data-sources")
router.include_router(crud_router, prefix="/data-sources")

__all__ = ["router"]
