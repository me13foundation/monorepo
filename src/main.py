from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from src.routes.health import router as health_router
from src.routes.resources import router as resources_router
from src.routes.genes import router as genes_router
from src.routes.dashboard import router as dashboard_router
from src.middleware.auth import AuthMiddleware
from src.middleware.rate_limit import EndpointRateLimitMiddleware
from src.routes.curation import router as curation_router


def create_app() -> FastAPI:
    """Instantiate the FastAPI application with middleware and routes."""
    app = FastAPI(
        title="MED13 Resource Library",
        version="0.1.0",
        description="Curated resource library for MED13 variants, "
        "phenotypes, and evidence.",
        contact={
            "name": "MED13 Foundation",
            "url": "https://med13foundation.org",
        },
        license_info={
            "name": "CC-BY 4.0",
            "url": "https://creativecommons.org/licenses/by/4.0/",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://med13foundation.org",
            "https://curate.med13foundation.org",
            "http://localhost:3000",
            "http://localhost:8080",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Add authentication middleware
    app.add_middleware(AuthMiddleware)

    # Add rate limiting middleware
    app.add_middleware(EndpointRateLimitMiddleware)

    # Root endpoint
    @app.get("/", summary="Welcome to MED13 Resource Library", tags=["info"])
    async def root() -> Dict[str, Any]:
        """Welcome endpoint with API information."""
        return {
            "message": "Welcome to the MED13 Resource Library API",
            "description": "Curated resource library for MED13 variants, "
            "phenotypes, and evidence",
            "version": "0.1.0",
            "documentation": "/docs",
            "health_check": "/health/",
            "resources": "/resources/",
            "genes": "/genes/",
            "authentication": {
                "type": "API Key",
                "header": "X-API-Key",
                "description": "Include API key in request headers for authentication",
            },
            "rate_limiting": {
                "description": "Rate limiting applied based on client IP",
                "headers": [
                    "X-RateLimit-Remaining",
                    "X-RateLimit-Limit",
                    "X-RateLimit-Reset",
                ],
            },
            "contact": "https://med13foundation.org",
            "license": "CC-BY 4.0",
        }

    app.include_router(health_router)
    app.include_router(resources_router)
    app.include_router(genes_router)
    app.include_router(dashboard_router)
    app.include_router(curation_router)

    return app


app = create_app()
