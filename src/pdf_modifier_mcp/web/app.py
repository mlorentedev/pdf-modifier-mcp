"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..logger import setup_logging
from .config import WebSettings
from .routes import ai_router, health_router, pdf_router

logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Application lifespan — startup and shutdown hooks."""
    logger.info("Web API starting up")
    yield
    logger.info("Web API shutting down")


def create_app(settings: WebSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional WebSettings override.

    Returns:
        Configured FastAPI app.
    """
    if settings is None:
        settings = WebSettings()

    app = FastAPI(
        title="PDF Modifier MCP",
        description="PDF text modification API with CLI and MCP interfaces.",
        version="1.5.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)
    app.include_router(pdf_router)
    app.include_router(ai_router)

    return app


# Default app instance (used by uvicorn)
app = create_app()
