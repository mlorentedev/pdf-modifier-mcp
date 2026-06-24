"""In-memory session manager with TTL-based expiration."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..logger import setup_logging

logger = setup_logging(__name__)


@dataclass
class SessionData:
    """Data associated with a web session."""

    session_id: str
    original_path: Path
    modified_path: Path | None = None
    structure: dict[str, Any] | None = None
    created_at: float = field(default_factory=lambda: __import__("time").time())


class SessionManager:
    """Manages in-memory sessions with TTL expiration.

    Each session tracks an uploaded PDF, its structure analysis,
    and any modifications. Expired sessions are cleaned up on access.

    Example:
        >>> mgr = SessionManager(ttl_seconds=3600)
        >>> sid = mgr.create()
        >>> session = mgr.get(sid)
        >>> mgr.delete(sid)
    """

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.Lock()

    def create(self, original_path: Path, modified_path: Path | None = None) -> str:
        """Create a new session.

        Args:
            original_path: Path to the uploaded PDF.
            modified_path: Optional path to a modified version.

        Returns:
            Session ID string.
        """
        session_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._sessions[session_id] = SessionData(
                session_id=session_id,
                original_path=original_path,
                modified_path=modified_path,
            )
        logger.info("Session created: %s", session_id)
        return session_id

    def get(self, session_id: str) -> SessionData | None:
        """Get a session by ID. Returns None if expired or not found."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            # Check TTL
            elapsed = __import__("time").time() - session.created_at
            if elapsed >= self._ttl_seconds and self._ttl_seconds > 0:
                del self._sessions[session_id]
                logger.info("Session expired: %s", session_id)
                return None
            return session

    def update_structure(self, session_id: str, structure: dict[str, Any]) -> bool:
        """Store structure analysis for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.structure = structure
            return True

    def set_modified_path(self, session_id: str, path: Path) -> bool:
        """Set the modified PDF path for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.modified_path = path
            return True

    def delete(self, session_id: str) -> bool:
        """Delete a session. Returns True if it existed."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info("Session deleted: %s", session_id)
                return True
            return False

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = __import__("time").time()
        expired: list[str] = []
        with self._lock:
            for sid, session in self._sessions.items():
                if now - session.created_at >= self._ttl_seconds and self._ttl_seconds > 0:
                    expired.append(sid)
            for sid in expired:
                del self._sessions[sid]
        if expired:
            logger.info("Cleaned up %d expired sessions", len(expired))
        return len(expired)

    def list_active(self) -> list[str]:
        """List all active session IDs."""
        with self._lock:
            now = __import__("time").time()
            # TTL <= 0 means no expiry (consistent with get() and cleanup_expired())
            if self._ttl_seconds <= 0:
                return list(self._sessions.keys())
            return [
                sid for sid, s in self._sessions.items() if now - s.created_at <= self._ttl_seconds
            ]
