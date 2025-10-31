from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.health import router as health_router
from src.routes.resources import router as resources_router


def create_app() -> FastAPI:
    """Instantiate the FastAPI application with middleware and routes."""
    app = FastAPI(title="MED13 Resource Library", version="0.1.0")

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

    app.include_router(health_router)
    app.include_router(resources_router)

    return app


app = create_app()
