"""API route definitions for the MED13 Resource Library."""

from .health import router as health_router
from .resources import router as resources_router
from .genes import router as genes_router

__all__ = ["health_router", "resources_router", "genes_router"]
