"""FastAPI router aggregation for data discovery endpoints."""

from fastapi import APIRouter

from .catalog import router as catalog_router
from .pubmed import router as pubmed_router
from .sessions import router as sessions_router
from .spaces import router as spaces_router
from .tests import router as tests_router

router = APIRouter(prefix="/data-discovery", tags=["data-discovery"])

router.include_router(sessions_router)
router.include_router(tests_router)
router.include_router(spaces_router)
router.include_router(catalog_router)
router.include_router(pubmed_router)

__all__ = ["router"]
