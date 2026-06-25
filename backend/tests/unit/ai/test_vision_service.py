"""Tests for VisionService (TDD: RED phase)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import fitz
import pytest

from pdf_modifier.ai.client import NaNClient
from pdf_modifier.ai.router import ModelRouter
from pdf_modifier.ai.throttle import Throttle
from pdf_modifier.ai.vision_service import VisionService


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a sample PDF for testing."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((100, 100), "Test document", fontsize=12)
    pdf_path = tmp_path / "sample.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def two_page_pdf(tmp_path: Path) -> Path:
    """Create a two-page PDF for comparison testing."""
    doc = fitz.open()
    for i in range(2):
        page = doc.new_page(width=595, height=842)
        page.insert_text((100, 100), f"Page {i + 1}: Original content", fontsize=12)
    pdf_path = tmp_path / "two_page.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def mock_client() -> AsyncMock:
    """Mock NaNClient with controllable responses."""
    client = AsyncMock(spec=NaNClient)
    client.is_configured = True
    return client


@pytest.fixture
def router() -> ModelRouter:
    """Real router for model selection."""
    return ModelRouter()


@pytest.fixture
def throttle() -> Throttle:
    """Real throttle with high concurrency for tests."""
    return Throttle(concurrency=10)


def make_ocr_response(text: str = "Extracted text") -> dict[str, Any]:
    """Helper to create a mock OCR response."""
    return {
        "choices": [
            {
                "message": {
                    "content": text,
                }
            }
        ]
    }


def make_signature_response(signatures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Helper to create a mock signature detection response."""
    import json

    if signatures is None:
        signatures = [
            {
                "page": 0,
                "bbox": [100, 200, 300, 400],
                "confidence": 0.92,
                "signature_type": "handwritten",
            }
        ]
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(signatures),
                }
            }
        ]
    }


def make_comparison_response(diffs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Helper to create a mock comparison response."""
    import json

    if diffs is None:
        diffs = [
            {
                "page": 0,
                "difference_type": "text_change",
                "description": "Changed Original to Modified",
                "old_value": "Original",
                "new_value": "Modified",
            }
        ]
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(diffs),
                }
            }
        ]
    }


class TestVisionServiceOCR:
    """Tests for OCR functionality."""

    @pytest.mark.asyncio
    async def test_ocr_returns_text_per_page(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """OCR should return extracted text for each page."""
        mock_client.chat.return_value = make_ocr_response("Hello World")

        async with VisionService(mock_client, router, throttle) as svc:
            result = await svc.ocr(sample_pdf, pages=[0])

        assert result.success is True
        assert len(result.pages) == 1
        assert result.pages[0].text == "Hello World"
        assert result.pages[0].page == 0

    @pytest.mark.asyncio
    async def test_ocr_calls_ai_with_image(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """OCR should send image to AI client."""
        mock_client.chat.return_value = make_ocr_response("Text")

        async with VisionService(mock_client, router, throttle) as svc:
            await svc.ocr(sample_pdf, pages=[0])

        mock_client.chat.assert_called_once()
        call_kwargs = mock_client.chat.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_ocr_uses_vision_model(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """OCR should use the vision model from router."""
        mock_client.chat.return_value = make_ocr_response("Text")

        async with VisionService(mock_client, router, throttle) as svc:
            await svc.ocr(sample_pdf, pages=[0])

        call_kwargs = mock_client.chat.call_args
        model = call_kwargs.kwargs.get("model") or call_kwargs[0][0]
        assert model == "mimo-v2.5"

    @pytest.mark.asyncio
    async def test_ocr_all_pages_by_default(
        self,
        two_page_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """OCR should process all pages when none specified."""
        mock_client.chat.return_value = make_ocr_response("Text")

        async with VisionService(mock_client, router, throttle) as svc:
            result = await svc.ocr(two_page_pdf)

        assert len(result.pages) == 2
        assert mock_client.chat.call_count == 2

    @pytest.mark.asyncio
    async def test_ocr_ai_failure_raises(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """OCR should raise AIVisionError on AI failure."""
        from pdf_modifier.ai.exceptions import AIVisionError

        mock_client.chat.side_effect = Exception("API error")

        async with VisionService(mock_client, router, throttle) as svc:
            with pytest.raises(AIVisionError, match="OCR failed"):
                await svc.ocr(sample_pdf, pages=[0])


class TestVisionServiceSignatures:
    """Tests for signature detection."""

    @pytest.mark.asyncio
    async def test_detect_signatures_returns_positions(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should return detected signature positions."""
        mock_client.chat.return_value = make_signature_response()

        async with VisionService(mock_client, router, throttle) as svc:
            result = await svc.detect_signatures(sample_pdf, pages=[0])

        assert result.success is True
        assert result.total_found == 1
        assert result.signatures[0].confidence == 0.92
        assert result.signatures[0].signature_type == "handwritten"

    @pytest.mark.asyncio
    async def test_detect_signatures_empty_when_none_found(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should return empty list when no signatures found."""
        mock_client.chat.return_value = make_signature_response([])

        async with VisionService(mock_client, router, throttle) as svc:
            result = await svc.detect_signatures(sample_pdf, pages=[0])

        assert result.total_found == 0
        assert len(result.signatures) == 0

    @pytest.mark.asyncio
    async def test_detect_signatures_ai_failure_raises(
        self,
        sample_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should raise AIVisionError on AI failure."""
        from pdf_modifier.ai.exceptions import AIVisionError

        mock_client.chat.side_effect = Exception("API error")

        async with VisionService(mock_client, router, throttle) as svc:
            with pytest.raises(AIVisionError, match="Signature detection failed"):
                await svc.detect_signatures(sample_pdf, pages=[0])


class TestVisionServiceComparison:
    """Tests for PDF comparison."""

    @pytest.mark.asyncio
    async def test_compare_returns_differences(
        self,
        two_page_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should return list of differences."""
        mock_client.chat.return_value = make_comparison_response()

        async with VisionService(mock_client, router, throttle) as svc:
            result = await svc.compare(two_page_pdf, two_page_pdf, pages=[0])

        assert result.success is True
        assert result.total_differences == 1
        assert result.identical is False

    @pytest.mark.asyncio
    async def test_compare_identical_pdfs(
        self,
        two_page_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should mark as identical when no differences found."""
        mock_client.chat.return_value = make_comparison_response([])

        async with VisionService(mock_client, router, throttle) as svc:
            result = await svc.compare(two_page_pdf, two_page_pdf, pages=[0])

        assert result.identical is True
        assert result.total_differences == 0

    @pytest.mark.asyncio
    async def test_compare_calls_ai_for_each_page(
        self,
        two_page_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should call AI once per page compared."""
        mock_client.chat.return_value = make_comparison_response()

        async with VisionService(mock_client, router, throttle) as svc:
            await svc.compare(two_page_pdf, two_page_pdf)  # All pages

        assert mock_client.chat.call_count == 2

    @pytest.mark.asyncio
    async def test_compare_ai_failure_raises(
        self,
        two_page_pdf: Path,
        mock_client: AsyncMock,
        router: ModelRouter,
        throttle: Throttle,
    ) -> None:
        """Should raise AIVisionError on AI failure."""
        from pdf_modifier.ai.exceptions import AIVisionError

        mock_client.chat.side_effect = Exception("API error")

        async with VisionService(mock_client, router, throttle) as svc:
            with pytest.raises(AIVisionError, match="PDF comparison failed"):
                await svc.compare(two_page_pdf, two_page_pdf, pages=[0])


class TestVisionServiceParsing:
    """Tests for JSON response parsing."""

    def test_parse_json_array_valid(self) -> None:
        """Should parse valid JSON array."""
        result = VisionService._parse_json_array('[{"key": "value"}]')
        assert len(result) == 1
        assert result[0]["key"] == "value"

    def test_parse_json_array_with_markdown(self) -> None:
        """Should handle markdown code blocks."""
        content = '```json\n[{"key": "value"}]\n```'
        result = VisionService._parse_json_array(content)
        assert len(result) == 1

    def test_parse_json_array_invalid_json(self) -> None:
        """Should return empty list for invalid JSON."""
        result = VisionService._parse_json_array("not json at all")
        assert result == []

    def test_parse_json_array_single_object(self) -> None:
        """Should wrap single object in list."""
        result = VisionService._parse_json_array('{"key": "value"}')
        assert len(result) == 1
