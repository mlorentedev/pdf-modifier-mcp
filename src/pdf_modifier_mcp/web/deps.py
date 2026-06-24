"""Dependency injection for web routes."""

from __future__ import annotations

from .config import WebSettings
from .session import SessionManager
from .storage import PDFStorage

_settings: WebSettings | None = None
_session_mgr: SessionManager | None = None
_storage: PDFStorage | None = None


def get_settings() -> WebSettings:
    """Get web settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = WebSettings()
    return _settings


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


def reset_deps() -> None:
    """Reset dependency singletons (for testing)."""
    global _settings, _session_mgr, _storage
    _settings = None
    _session_mgr = None
    _storage = None
