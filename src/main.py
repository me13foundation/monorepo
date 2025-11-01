from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from src.routes.health import router as health_router
from src.routes.resources import router as resources_router


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
            "contact": "https://med13foundation.org",
            "license": "CC-BY 4.0",
        }

    app.include_router(health_router)
    app.include_router(resources_router)

    return app


app = create_app()
