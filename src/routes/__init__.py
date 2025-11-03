"""API route definitions for the MED13 Resource Library."""

from .health import router as health_router
from .resources import router as resources_router
from .genes import router as genes_router
from .variants import router as variants_router
from .phenotypes import router as phenotypes_router
from .evidence import router as evidence_router
from .search import router as search_router
from .export import router as export_router

__all__ = [
    "health_router",
    "resources_router",
    "genes_router",
    "variants_router",
    "phenotypes_router",
    "evidence_router",
    "search_router",
    "export_router",
]
