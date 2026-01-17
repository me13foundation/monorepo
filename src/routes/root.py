"""Root info route for the MED13 Resource Library API."""

from fastapi import APIRouter

from src.type_definitions.common import JSONObject

router = APIRouter(tags=["info"])


@router.get("/", summary="Welcome to MED13 Resource Library", tags=["info"])
async def root() -> JSONObject:
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


__all__ = ["router"]
