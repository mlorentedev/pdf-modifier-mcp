"""Tests for web session manager."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from pdf_modifier_mcp.web.config import WebSettings
from pdf_modifier_mcp.web.session import SessionManager

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


class TestSessionManager:
    """Session manager tests."""

    def test_create_returns_session_id(self) -> None:
        mgr = SessionManager(ttl_seconds=3600)
        sid = mgr.create(Path("/tmp/test.pdf"))
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_get_returns_session(self) -> None:
        mgr = SessionManager(ttl_seconds=3600)
        sid = mgr.create(Path("/tmp/test.pdf"))
        session = mgr.get(sid)
        assert session is not None
        assert session.session_id == sid

    def test_get_expired_returns_none(self) -> None:
        mgr = SessionManager(ttl_seconds=1)
        sid = mgr.create(Path("/tmp/test.pdf"))
        time.sleep(1.1)
        session = mgr.get(sid)
        assert session is None

    def test_get_nonexistent_returns_none(self) -> None:
        mgr = SessionManager()
        assert mgr.get("nonexistent") is None

    def test_update_structure(self) -> None:
        mgr = SessionManager()
        sid = mgr.create(Path("/tmp/test.pdf"))
        result = mgr.update_structure(sid, {"pages": 1})
        assert result is True
        session = mgr.get(sid)
        assert session is not None
        assert session.structure == {"pages": 1}

    def test_update_structure_wrong_session(self) -> None:
        mgr = SessionManager()
        mgr.create(Path("/tmp/test.pdf"))
        result = mgr.update_structure("wrong_id", {"pages": 1})
        assert result is False

    def test_set_modified_path(self) -> None:
        mgr = SessionManager()
        sid = mgr.create(Path("/tmp/test.pdf"))
        result = mgr.set_modified_path(sid, Path("/tmp/modified.pdf"))
        assert result is True
        session = mgr.get(sid)
        assert session is not None
        assert session.modified_path == Path("/tmp/modified.pdf")

    def test_delete_existing(self) -> None:
        mgr = SessionManager()
        sid = mgr.create(Path("/tmp/test.pdf"))
        result = mgr.delete(sid)
        assert result is True
        assert mgr.get(sid) is None

    def test_delete_nonexistent(self) -> None:
        mgr = SessionManager()
        result = mgr.delete("nonexistent")
        assert result is False

    def test_cleanup_expired(self) -> None:
        mgr = SessionManager(ttl_seconds=1)
        mgr.create(Path("/tmp/test1.pdf"))
        mgr.create(Path("/tmp/test2.pdf"))
        time.sleep(1.1)
        count = mgr.cleanup_expired()
        assert count == 2

    def test_list_active(self) -> None:
        mgr = SessionManager(ttl_seconds=3600)
        sid1 = mgr.create(Path("/tmp/test1.pdf"))
        sid2 = mgr.create(Path("/tmp/test2.pdf"))
        active = mgr.list_active()
        assert sid1 in active
        assert sid2 in active

    def test_env_override(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setenv("WEB_SESSION_TTL_SECONDS", "7200")
        settings = WebSettings()
        assert settings.session_ttl_seconds == 7200
