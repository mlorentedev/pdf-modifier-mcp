"""Tests for vision endpoints with feature flags."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import fitz
import pytest
from fastapi.testclient import TestClient

from pdf_modifier.ai.models import OCRPageResult, OCRResult
from pdf_modifier.web.app import create_app
from pdf_modifier.web.config import FeatureFlags
from pdf_modifier.web.deps import get_feature_flags, get_session_pdf_path, reset_deps


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((100, 100), "Test OCR content", fontsize=12)
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def _client(flags: FeatureFlags, pdf_path: str | None = None) -> TestClient:
    """Create a TestClient with dependency overrides."""
    reset_deps()
    app = create_app()
    app.dependency_overrides[get_feature_flags] = lambda: flags
    if pdf_path is not None:
        app.dependency_overrides[get_session_pdf_path] = lambda session_id: pdf_path
    return TestClient(app)


class TestFeatureFlagsConfig:
    def test_default_flags_are_disabled(self) -> None:
        flags = FeatureFlags()
        assert flags.vision_enabled is False
        assert flags.ocr_enabled is False
        assert flags.signature_detection_enabled is False
        assert flags.pdf_comparison_enabled is False

    def test_vision_available(self) -> None:
        assert FeatureFlags(vision_enabled=True).vision_available is True
        assert FeatureFlags(vision_enabled=False).vision_available is False

    def test_ocr_available_requires_both(self) -> None:
        assert FeatureFlags(vision_enabled=True, ocr_enabled=True).ocr_available is True
        assert FeatureFlags(vision_enabled=True, ocr_enabled=False).ocr_available is False
        assert FeatureFlags(vision_enabled=False, ocr_enabled=True).ocr_available is False

    def test_signature_detection_available_requires_both(self) -> None:
        assert (
            FeatureFlags(
                vision_enabled=True, signature_detection_enabled=True
            ).signature_detection_available
            is True
        )
        assert (
            FeatureFlags(
                vision_enabled=True, signature_detection_enabled=False
            ).signature_detection_available
            is False
        )

    def test_pdf_comparison_available_requires_both(self) -> None:
        assert (
            FeatureFlags(vision_enabled=True, pdf_comparison_enabled=True).pdf_comparison_available
            is True
        )
        assert (
            FeatureFlags(vision_enabled=True, pdf_comparison_enabled=False).pdf_comparison_available
            is False
        )


class TestOCREndpoint:
    def test_disabled_returns_503(self, sample_pdf: Path) -> None:
        client = _client(FeatureFlags(vision_enabled=False), str(sample_pdf))
        response = client.post("/api/ai/session-123/ocr")
        assert response.status_code == 503
        assert "OCR not available" in response.json()["detail"]["error"]

    def test_enabled_calls_service(self, sample_pdf: Path) -> None:
        client = _client(FeatureFlags(vision_enabled=True, ocr_enabled=True), str(sample_pdf))
        mock_service = AsyncMock()
        mock_service.ocr.return_value = OCRResult(
            pages=[OCRPageResult(page=0, text="Hello", confidence=0.9, has_text_layer=False)],
            total_pages=1,
            model="mimo-v2.5",
        )
        with patch("pdf_modifier.web.routes.vision.get_vision_service", return_value=mock_service):
            response = client.post("/api/ai/abc123/ocr")
        assert response.status_code == 200
        assert response.json()["pages"][0]["text"] == "Hello"

    def test_no_pdf_returns_404(self) -> None:
        client = _client(FeatureFlags(vision_enabled=True, ocr_enabled=True))
        response = client.post("/api/ai/abc123/ocr")
        assert response.status_code == 404


class TestSignatureDetectionEndpoint:
    def test_disabled_returns_503(self, sample_pdf: Path) -> None:
        client = _client(FeatureFlags(vision_enabled=False), str(sample_pdf))
        response = client.post("/api/ai/session-123/detect-signatures")
        assert response.status_code == 503
        assert "Signature detection not available" in response.json()["detail"]["error"]

    def test_enabled_calls_service(self, sample_pdf: Path) -> None:
        client = _client(
            FeatureFlags(vision_enabled=True, signature_detection_enabled=True), str(sample_pdf)
        )
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {
            "success": True,
            "signatures": [],
            "total_found": 0,
            "model": "mimo-v2.5",
        }
        mock_service = AsyncMock()
        mock_service.detect_signatures.return_value = mock_result
        with patch("pdf_modifier.web.routes.vision.get_vision_service", return_value=mock_service):
            response = client.post("/api/ai/abc123/detect-signatures")
        assert response.status_code == 200
        assert response.json()["total_found"] == 0


class TestPDFComparisonEndpoint:
    def test_disabled_returns_503(self) -> None:
        client = _client(FeatureFlags(vision_enabled=False, pdf_comparison_enabled=False))
        response = client.post("/api/ai/compare?session_id_a=aaa", json={"session_id_b": "bbb"})
        assert response.status_code == 503
        assert "PDF comparison not available" in response.json()["detail"]["error"]

    def test_missing_session_a_returns_422(self) -> None:
        client = _client(FeatureFlags(vision_enabled=True, pdf_comparison_enabled=True))
        response = client.post("/api/ai/compare", json={"session_id_b": "bbb"})
        assert response.status_code == 422
