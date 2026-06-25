"""Web routes package."""

from .ai import router as ai_router
from .health import router as health_router
from .pdf import router as pdf_router
from .vision import router as vision_router

__all__ = ["health_router", "pdf_router", "ai_router", "vision_router"]
