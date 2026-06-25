"""Tests for AI vision capabilities (TDD: RED phase)."""

from __future__ import annotations

import base64
from pathlib import Path

import fitz
import pytest

from pdf_modifier.ai.vision import (
    ImageFormat,
    ImageOptions,
    encode_image_base64,
    pdf_page_to_image,
)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a sample PDF with text for testing."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    page.insert_text((100, 100), "Hello World", fontsize=12)
    page.insert_text((100, 200), "Test document for OCR", fontsize=14)
    pdf_path = tmp_path / "sample.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    """Create a multi-page PDF for testing."""
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        page.insert_text((100, 100), f"Page {i + 1} content", fontsize=12)
    pdf_path = tmp_path / "multi_page.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


class TestPdfPageToImage:
    """Tests for PDF page to image conversion."""

    def test_convert_page_to_png_returns_bytes(self, sample_pdf: Path) -> None:
        """T1.1: Converting a page should return image bytes."""
        image_bytes = pdf_page_to_image(sample_pdf, page_num=0)
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_convert_page_returns_valid_png(self, sample_pdf: Path) -> None:
        """T1.1: Output should be valid PNG format."""
        image_bytes = pdf_page_to_image(sample_pdf, page_num=0)
        # PNG magic bytes: \x89PNG
        assert image_bytes[:4] == b"\x89PNG"

    def test_convert_page_respects_dpi(self, sample_pdf: Path) -> None:
        """T1.1: Different DPI should produce different sized images."""
        image_low = pdf_page_to_image(sample_pdf, page_num=0, dpi=72)
        image_high = pdf_page_to_image(sample_pdf, page_num=0, dpi=150)
        # Higher DPI = larger image
        assert len(image_high) > len(image_low)

    def test_convert_page_default_dpi(self, sample_pdf: Path) -> None:
        """T1.1: Default DPI should be 150."""
        image_bytes = pdf_page_to_image(sample_pdf, page_num=0)
        assert len(image_bytes) > 0

    def test_convert_page_invalid_page_raises(self, sample_pdf: Path) -> None:
        """T1.1: Invalid page number should raise IndexError."""
        with pytest.raises(IndexError):
            pdf_page_to_image(sample_pdf, page_num=999)

    def test_convert_page_negative_page_raises(self, sample_pdf: Path) -> None:
        """T1.1: Negative page number should raise IndexError."""
        with pytest.raises(IndexError):
            pdf_page_to_image(sample_pdf, page_num=-1)

    def test_convert_multi_page_pdf(self, multi_page_pdf: Path) -> None:
        """T1.1: Should handle multi-page PDFs correctly."""
        for i in range(3):
            image_bytes = pdf_page_to_image(multi_page_pdf, page_num=i)
            assert len(image_bytes) > 0


class TestImageOptions:
    """Tests for ImageOptions dataclass."""

    def test_default_options(self) -> None:
        """Default options should have sensible defaults."""
        opts = ImageOptions()
        assert opts.dpi == 150
        assert opts.format == ImageFormat.PNG
        assert opts.quality == 85

    def test_custom_options(self) -> None:
        """Custom options should override defaults."""
        opts = ImageOptions(dpi=300, format=ImageFormat.JPEG, quality=95)
        assert opts.dpi == 300
        assert opts.format == ImageFormat.JPEG
        assert opts.quality == 95

    def test_options_with_image_bytes(self, sample_pdf: Path) -> None:
        """Options should work with pdf_page_to_image."""
        opts = ImageOptions(dpi=72)
        image_bytes = pdf_page_to_image(sample_pdf, page_num=0, options=opts)
        assert len(image_bytes) > 0


class TestImageOptionsValidation:
    """Tests for ImageOptions validation."""

    def test_dpi_too_low_raises(self) -> None:
        """DPI below 72 should raise ValueError."""
        with pytest.raises(ValueError, match="dpi must be between"):
            ImageOptions(dpi=50)

    def test_dpi_too_high_raises(self) -> None:
        """DPI above 300 should raise ValueError."""
        with pytest.raises(ValueError, match="dpi must be between"):
            ImageOptions(dpi=400)

    def test_quality_too_low_raises(self) -> None:
        """Quality below 1 should raise ValueError."""
        with pytest.raises(ValueError, match="quality must be between"):
            ImageOptions(quality=0)

    def test_quality_too_high_raises(self) -> None:
        """Quality above 100 should raise ValueError."""
        with pytest.raises(ValueError, match="quality must be between"):
            ImageOptions(quality=101)

    def test_dpi_boundaries_valid(self) -> None:
        """Boundary DPI values should be valid."""
        opts_low = ImageOptions(dpi=72)
        opts_high = ImageOptions(dpi=300)
        assert opts_low.dpi == 72
        assert opts_high.dpi == 300

    def test_quality_boundaries_valid(self) -> None:
        """Boundary quality values should be valid."""
        opts_low = ImageOptions(quality=1)
        opts_high = ImageOptions(quality=100)
        assert opts_low.quality == 1
        assert opts_high.quality == 100


class TestEncodeImageBase64:
    """Tests for Base64 image encoding."""

    def test_encode_returns_data_uri(self) -> None:
        """T1.2: Encoding should return data URI format."""
        image_bytes = b"\x89PNG" + b"\x00" * 100  # Fake PNG
        result = encode_image_base64(image_bytes)
        assert result.startswith("data:image/png;base64,")

    def test_encode_preserves_data(self) -> None:
        """T1.2: Encoding should preserve original data."""
        image_bytes = b"test image data"
        result = encode_image_base64(image_bytes)
        # Extract base64 part
        b64_data = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_data)
        assert decoded == image_bytes

    def test_encode_empty_bytes(self) -> None:
        """T1.2: Should handle empty bytes."""
        result = encode_image_base64(b"")
        assert result.startswith("data:image/png;base64,")

    def test_encode_with_format_hint(self) -> None:
        """T1.2: Should use format hint for MIME type."""
        image_bytes = b"fake jpeg data"
        result = encode_image_base64(image_bytes, format_hint="jpeg")
        assert result.startswith("data:image/jpeg;base64,")

    def test_encode_from_pdf_page(self, sample_pdf: Path) -> None:
        """T1.2: Full pipeline: PDF -> image -> base64."""
        image_bytes = pdf_page_to_image(sample_pdf, page_num=0)
        data_uri = encode_image_base64(image_bytes)
        assert data_uri.startswith("data:image/png;base64,")
        # Verify it's valid base64
        b64_data = data_uri.split(",", 1)[1]
        decoded = base64.b64decode(b64_data)
        assert decoded == image_bytes


class TestPdfPageToDataUri:
    """Tests for the convenience function."""

    def test_returns_data_uri(self, sample_pdf: Path) -> None:
        """Should return a valid data URI."""
        from pdf_modifier.ai.vision import pdf_page_to_data_uri

        result = pdf_page_to_data_uri(sample_pdf, page_num=0)
        assert result.startswith("data:image/png;base64,")

    def test_with_custom_options(self, sample_pdf: Path) -> None:
        """Should work with custom options."""
        from pdf_modifier.ai.vision import ImageOptions, pdf_page_to_data_uri

        opts = ImageOptions(dpi=72, format=ImageFormat.JPEG, quality=50)
        result = pdf_page_to_data_uri(sample_pdf, page_num=0, options=opts)
        assert result.startswith("data:image/jpeg;base64,")


class TestGetPdfPageCount:
    """Tests for page count utility."""

    def test_single_page_pdf(self, sample_pdf: Path) -> None:
        """Single page PDF should return 1."""
        from pdf_modifier.ai.vision import get_pdf_page_count

        assert get_pdf_page_count(sample_pdf) == 1

    def test_multi_page_pdf(self, multi_page_pdf: Path) -> None:
        """Multi-page PDF should return correct count."""
        from pdf_modifier.ai.vision import get_pdf_page_count

        assert get_pdf_page_count(multi_page_pdf) == 3

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """Non-existent file should raise FileNotFoundError."""
        from pdf_modifier.ai.vision import get_pdf_page_count

        with pytest.raises(FileNotFoundError):
            get_pdf_page_count(tmp_path / "nonexistent.pdf")


class TestPdfPageToImageEdgeCases:
    """Additional edge case tests for coverage."""

    def test_nonexistent_file_raises(self, tmp_path: Path) -> None:
        """Non-existent PDF should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            pdf_page_to_image(tmp_path / "nonexistent.pdf", page_num=0)

    def test_jpeg_format(self, sample_pdf: Path) -> None:
        """Should support JPEG format output."""
        opts = ImageOptions(format=ImageFormat.JPEG, quality=75)
        image_bytes = pdf_page_to_image(sample_pdf, page_num=0, options=opts)
        assert len(image_bytes) > 0
        # JPEG starts with FF D8
        assert image_bytes[:2] == b"\xff\xd8"
