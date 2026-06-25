"""Dependency injection for web routes."""

from __future__ import annotations

from ..ai.client import NaNClient
from ..ai.router import ModelRouter
from ..ai.throttle import Throttle
from ..ai.vision_service import VisionService
from .config import FeatureFlags, WebSettings
from .session import SessionManager
from .storage import PDFStorage

_settings: WebSettings | None = None
_feature_flags: FeatureFlags | None = None
_session_mgr: SessionManager | None = None
_storage: PDFStorage | None = None
_nan_client: NaNClient | None = None
_router: ModelRouter | None = None
_throttle: Throttle | None = None
_vision_service: VisionService | None = None


def get_settings() -> WebSettings:
    """Get web settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = WebSettings()
    return _settings


def get_feature_flags() -> FeatureFlags:
    """Get feature flags (singleton)."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def get_session_manager() -> SessionManager:
    """Get session manager instance (singleton)."""
    global _session_mgr
    if _session_mgr is None:
        settings = get_settings()
        _session_mgr = SessionManager(ttl_seconds=settings.session_ttl_seconds)
    return _session_mgr


def get_storage() -> PDFStorage:
    """Get storage instance (singleton)."""
    global _storage
    if _storage is None:
        settings = get_settings()
        _storage = PDFStorage(settings.storage_dir)
    return _storage


def get_nan_client() -> NaNClient:
    """Get NaN Cloud client (singleton)."""
    global _nan_client
    if _nan_client is None:
        _nan_client = NaNClient()
    return _nan_client


def get_router() -> ModelRouter:
    """Get model router (singleton)."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def get_throttle() -> Throttle:
    """Get throttle instance (singleton)."""
    global _throttle
    if _throttle is None:
        _throttle = Throttle()
    return _throttle


def get_vision_service() -> VisionService:
    """Get vision service (singleton)."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService(
            client=get_nan_client(),
            router=get_router(),
            throttle=get_throttle(),
        )
    return _vision_service


def get_session_pdf_path(session_id: str) -> str | None:
    """Get PDF path for a session (FastAPI dependency).

    Returns:
        PDF path string, or None if session/PDF not found.
    """
    storage = get_storage()
    try:
        pdf_path = storage.get_pdf(session_id)
        return str(pdf_path) if pdf_path else None
    except Exception:
        return None


def reset_deps() -> None:
    """Reset dependency singletons (for testing)."""
    global _settings, _feature_flags, _session_mgr, _storage
    global _nan_client, _router, _throttle, _vision_service
    _settings = None
    _feature_flags = None
    _session_mgr = None
    _storage = None
    _nan_client = None
    _router = None
    _throttle = None
    _vision_service = None
