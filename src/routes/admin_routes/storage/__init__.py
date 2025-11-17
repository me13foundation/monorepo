"""Storage admin router."""

from fastapi import APIRouter

from .configurations import router as configurations_router

router = APIRouter()
router.include_router(configurations_router)

__all__ = ["router"]
