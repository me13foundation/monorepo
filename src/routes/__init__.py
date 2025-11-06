"""API route definitions for the MED13 Resource Library."""

from .evidence import router as evidence_router
from .export import router as export_router
from .genes import router as genes_router
from .health import router as health_router
from .phenotypes import router as phenotypes_router
from .resources import router as resources_router
from .search import router as search_router
from .variants import router as variants_router

__all__ = [
    "evidence_router",
    "export_router",
    "genes_router",
    "health_router",
    "phenotypes_router",
    "resources_router",
    "search_router",
    "variants_router",
]
