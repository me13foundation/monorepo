"""Router aggregation for admin data source endpoints."""

from fastapi import APIRouter

from .ai_testing import router as ai_testing_router
from .crud import router as crud_router
from .history import router as history_router
from .listing import router as listing_router
from .scheduling import router as scheduling_router

router = APIRouter()

router.include_router(listing_router, prefix="/data-sources")
router.include_router(crud_router, prefix="/data-sources")
router.include_router(scheduling_router, prefix="/data-sources")
router.include_router(history_router, prefix="/data-sources")
router.include_router(ai_testing_router, prefix="/data-sources")

__all__ = ["router"]
