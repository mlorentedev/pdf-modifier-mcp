"""Tests for PDFAnalyzer embedded font extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import fitz
import pytest

from pdf_modifier_mcp.core.analyzer import PDFAnalyzer
from pdf_modifier_mcp.core.exceptions import PDFNotFoundError
from pdf_modifier_mcp.core.models import EmbeddedFontInfo


class TestExtractEmbeddedFonts:
    """Tests for PDFAnalyzer.extract_embedded_fonts()."""

    def _create_pdf_with_custom_font(self, tmp_path: Path) -> Path:
        """Create a PDF with an embedded custom font."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "Hello Custom Font",
            fontname="myfont",
            fontfile="C:/Windows/Fonts/arial.ttf",
            fontsize=12,
        )
        pdf_path = tmp_path / "custom_font.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def _create_pdf_with_base14_only(self, tmp_path: Path) -> Path:
        """Create a PDF with only Base 14 fonts."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello Base14", fontname="helv", fontsize=12)
        pdf_path = tmp_path / "base14.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_extract_embedded_fonts_returns_list(self, tmp_path: Path) -> None:
        """extract_embedded_fonts returns a list."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        assert isinstance(result, list)

    def test_extract_embedded_fonts_finds_custom_font(self, tmp_path: Path) -> None:
        """Custom embedded fonts are detected."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        assert len(result) >= 1

    def test_extract_embedded_fonts_has_correct_fields(self, tmp_path: Path) -> None:
        """Each EmbeddedFontInfo has required fields."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        for info in result:
            assert isinstance(info, EmbeddedFontInfo)
            assert info.name  # non-empty name
            assert info.type  # e.g. TrueType, Type0
            assert info.subtype  # e.g. ttf
            assert isinstance(info.buffer, bytes)

    def test_extract_embedded_fonts_buffer_not_empty(self, tmp_path: Path) -> None:
        """Embedded font buffers contain data."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        for info in result:
            assert len(info.buffer) > 0

    def test_extract_embedded_fonts_type0_for_custom(self, tmp_path: Path) -> None:
        """Custom fonts are Type0 (not Type1)."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        # At least one font should be Type0 (custom embedded)
        has_type0 = any(info.type == "Type0" for info in result)
        assert has_type0, f"Expected Type0 font, got: {[info.type for info in result]}"

    def test_extract_embedded_fonts_page_numbers(self, tmp_path: Path) -> None:
        """Page numbers are tracked correctly."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        for info in result:
            assert all(p >= 1 for p in info.page_numbers)

    def test_extract_embedded_fonts_empty_for_base14_only(self, tmp_path: Path) -> None:
        """Base 14 fonts only → no embedded fonts (they are system fonts)."""
        pdf_path = self._create_pdf_with_base14_only(tmp_path)
        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        # Base 14 fonts (Type1) are not embedded — they use system encoding
        # The result should be empty or only contain Type1 fonts
        type0_count = sum(1 for info in result if info.type == "Type0")
        assert type0_count == 0, f"Expected no Type0 fonts, got: {result}"

    def test_extract_embedded_fonts_multiple_pages(self, tmp_path: Path) -> None:
        """Font embedded across multiple pages is tracked."""
        doc = fitz.open()
        page1 = doc.new_page()
        page1.insert_text(
            (72, 72),
            "Page 1",
            fontname="myfont",
            fontfile="C:/Windows/Fonts/arial.ttf",
            fontsize=12,
        )
        page2 = doc.new_page()
        page2.insert_text(
            (72, 72),
            "Page 2",
            fontname="myfont",
            fontfile="C:/Windows/Fonts/arial.ttf",
            fontsize=12,
        )
        pdf_path = tmp_path / "multi_page.pdf"
        doc.save(str(pdf_path))
        doc.close()

        analyzer = PDFAnalyzer(str(pdf_path))
        result = analyzer.extract_embedded_fonts()
        # Should find the font
        assert len(result) >= 1
        # Page numbers should include both pages
        all_pages = set()
        for info in result:
            all_pages.update(info.page_numbers)
        assert 1 in all_pages
        assert 2 in all_pages

    def test_extract_embedded_fonts_invalid_file_raises(self, tmp_path: Path) -> None:
        """Non-existent PDF raises PDFNotFoundError."""
        analyzer = PDFAnalyzer(str(tmp_path / "missing.pdf"))
        with pytest.raises(PDFNotFoundError):
            analyzer.extract_embedded_fonts()
