from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.container import container, initialize_legacy_session
from src.database.seed import (
    ensure_default_research_space_seeded,
    ensure_source_catalog_seeded,
)
from src.database.session import get_session
from src.middleware.auth import AuthMiddleware
from src.middleware.jwt_auth import JWTAuthMiddleware
from src.middleware.rate_limit import EndpointRateLimitMiddleware
from src.routes.admin import router as admin_router
from src.routes.auth import auth_router
from src.routes.curation import router as curation_router
from src.routes.dashboard import router as dashboard_router
from src.routes.data_discovery import router as data_discovery_router
from src.routes.evidence import router as evidence_router
from src.routes.export import router as export_router
from src.routes.genes import router as genes_router
from src.routes.health import router as health_router
from src.routes.phenotypes import router as phenotypes_router

# Import models to ensure they're registered with SQLAlchemy
from src.routes.research_spaces import research_spaces_router
from src.routes.resources import router as resources_router
from src.routes.search import router as search_router
from src.routes.users import users_router
from src.routes.variants import router as variants_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup
    # Initialize legacy session for backward compatibility
    legacy_session = next(get_session())
    try:
        initialize_legacy_session(legacy_session)
        ensure_source_catalog_seeded(legacy_session)
        ensure_default_research_space_seeded(legacy_session)
        legacy_session.commit()
        yield
    except Exception:
        legacy_session.rollback()
        raise
    finally:
        legacy_session.close()
        await container.engine.dispose()


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
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://med13foundation.org",
            "https://curate.med13foundation.org",
            "https://admin.med13foundation.org",
            "http://localhost:3000",  # Next.js admin interface
            "http://localhost:3001",  # Next.js admin interface (alternate port)
            "http://localhost:8050",  # Dash curation interface
            "http://localhost:8080",  # FastAPI backend
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        allow_credentials=True,
        expose_headers=["*"],
    )

    # Add legacy API key authentication middleware (runs first)
    app.add_middleware(AuthMiddleware)

    # Add JWT authentication middleware
    app.add_middleware(JWTAuthMiddleware)

    # Add rate limiting middleware
    app.add_middleware(EndpointRateLimitMiddleware)

    # Root endpoint
    @app.get("/", summary="Welcome to MED13 Resource Library", tags=["info"])
    async def root() -> dict[str, Any]:
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
                "type": "JWT Bearer Token",
                "header": "Authorization",
                "format": "Bearer {token}",
                "login_endpoint": "/auth/login",
                "description": "Use JWT tokens obtained from /auth/login for API authentication",
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
    app.include_router(variants_router)
    app.include_router(phenotypes_router)
    app.include_router(evidence_router)
    app.include_router(search_router)
    app.include_router(export_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(curation_router)
    app.include_router(research_spaces_router)
    app.include_router(data_discovery_router)

    # Authentication routes
    app.include_router(auth_router)
    app.include_router(users_router)

    return app


app = create_app()
