"""Tests for web app and routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pdf_modifier.web.app import create_app
from pdf_modifier.web.config import WebSettings
from pdf_modifier.web.deps import reset_deps
from tests.conftest import create_pdf


@pytest.fixture(autouse=True)
def reset_web_deps() -> None:
    """Reset web dependency singletons before each test."""
    reset_deps()


def _make_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\ntrailer\n<< /Size 1 >>\nstartxref\n0\n%%EOF\n"


class TestHealthEndpoint:
    """Health check tests."""

    def test_health_returns_ok(self, tmp_path: Path) -> None:
        # Pre-configure deps
        import pdf_modifier.web.deps as deps

        deps._settings = WebSettings(storage_dir=str(tmp_path / "storage"))
        deps._session_mgr = None
        deps._storage = None

        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPDFUpload:
    """PDF upload endpoint tests."""

    @pytest.fixture
    def app(self, tmp_path: Path) -> object:
        import pdf_modifier.web.deps as deps

        deps._settings = WebSettings(storage_dir=str(tmp_path / "storage"))
        deps._session_mgr = None
        deps._storage = None
        return create_app()

    def test_upload_pdf_returns_session_id(self, app: object, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "upload.pdf", text="Hello World")
        client = TestClient(app)
        with open(pdf, "rb") as f:
            response = client.post(
                "/api/pdf/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_upload_non_pdf_returns_400(self, app: object, tmp_path: Path) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/pdf/upload",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_oversized_returns_413(self, app: object, tmp_path: Path) -> None:
        client = TestClient(app)
        # 200 MB of null bytes
        large_content = b"\x00" * (200 * 1024 * 1024)
        response = client.post(
            "/api/pdf/upload",
            files={"file": ("big.pdf", large_content, "application/pdf")},
        )
        assert response.status_code == 413


class TestPDFStructure:
    """PDF structure endpoint tests."""

    @pytest.fixture
    def app(self, tmp_path: Path) -> object:
        import pdf_modifier.web.deps as deps

        deps._settings = WebSettings(storage_dir=str(tmp_path / "storage"))
        deps._session_mgr = None
        deps._storage = None
        return create_app()

    def test_get_structure_returns_pdf_data(self, app: object, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "struct.pdf", text="Hello World")
        client = TestClient(app)
        with open(pdf, "rb") as f:
            upload_resp = client.post(
                "/api/pdf/upload",
                files={"file": ("struct.pdf", f, "application/pdf")},
            )
        session_id = upload_resp.json()["session_id"]

        response = client.get(f"/api/pdf/{session_id}/structure")
        assert response.status_code == 200
        data = response.json()
        assert "total_pages" in data
        assert "pages" in data
        assert data["success"] is True

    def test_get_structure_nonexistent_session(self, app: object) -> None:
        client = TestClient(app)
        response = client.get("/api/pdf/nonexistent/structure")
        assert response.status_code == 404


class TestPDFReplace:
    """PDF replace endpoint tests."""

    @pytest.fixture
    def app(self, tmp_path: Path) -> object:
        import pdf_modifier.web.deps as deps

        deps._settings = WebSettings(storage_dir=str(tmp_path / "storage"))
        deps._session_mgr = None
        deps._storage = None
        return create_app()

    def test_replace_returns_modification_result(self, app: object, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "replace.pdf", text="Hello World")
        client = TestClient(app)
        with open(pdf, "rb") as f:
            upload_resp = client.post(
                "/api/pdf/upload",
                files={"file": ("replace.pdf", f, "application/pdf")},
            )
        session_id = upload_resp.json()["session_id"]

        response = client.post(
            f"/api/pdf/{session_id}/replace",
            json={"replacements": {"Hello": "Goodbye"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "replacements_made" in data


class TestPDFDownload:
    """PDF download endpoint tests."""

    @pytest.fixture
    def app(self, tmp_path: Path) -> object:
        import pdf_modifier.web.deps as deps

        deps._settings = WebSettings(storage_dir=str(tmp_path / "storage"))
        deps._session_mgr = None
        deps._storage = None
        return create_app()

    def test_download_returns_pdf(self, app: object, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "download.pdf", text="Hello World")
        client = TestClient(app)
        with open(pdf, "rb") as f:
            upload_resp = client.post(
                "/api/pdf/upload",
                files={"file": ("download.pdf", f, "application/pdf")},
            )
        session_id = upload_resp.json()["session_id"]

        response = client.get(f"/api/pdf/{session_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_download_no_modification_returns_original(self, app: object, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "orig.pdf", text="Original")
        client = TestClient(app)
        with open(pdf, "rb") as f:
            upload_resp = client.post(
                "/api/pdf/upload",
                files={"file": ("orig.pdf", f, "application/pdf")},
            )
        session_id = upload_resp.json()["session_id"]

        response = client.get(f"/api/pdf/{session_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        # Should return a valid PDF (modified doesn't exist, returns original)


class TestPDFDelete:
    """PDF delete endpoint tests."""

    @pytest.fixture
    def app(self, tmp_path: Path) -> object:
        import pdf_modifier.web.deps as deps

        deps._settings = WebSettings(storage_dir=str(tmp_path / "storage"))
        deps._session_mgr = None
        deps._storage = None
        return create_app()

    def test_delete_removes_session_and_files(self, app: object, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "delete.pdf", text="Hello")
        client = TestClient(app)
        with open(pdf, "rb") as f:
            upload_resp = client.post(
                "/api/pdf/upload",
                files={"file": ("delete.pdf", f, "application/pdf")},
            )
        session_id = upload_resp.json()["session_id"]

        response = client.delete(f"/api/pdf/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_nonexistent_returns_404(self, app: object) -> None:
        client = TestClient(app)
        response = client.delete("/api/pdf/nonexistent")
        assert response.status_code == 404
