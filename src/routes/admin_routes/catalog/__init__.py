"""Router aggregation for admin data catalog endpoints."""

from fastapi import APIRouter

from .availability import router as availability_router
from .entries import router as entries_router

router = APIRouter(prefix="/data-catalog")

router.include_router(entries_router)
router.include_router(availability_router)

__all__ = ["router"]
