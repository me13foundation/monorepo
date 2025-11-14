"""Router aggregation for admin template endpoints."""

from fastapi import APIRouter

from .listing import router as listing_router
from .mutations import router as mutations_router

router = APIRouter()

router.include_router(listing_router)
router.include_router(mutations_router)

__all__ = ["router"]
