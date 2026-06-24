"""Tests for MCP embedded font tools."""

from __future__ import annotations

import json
import os
from pathlib import Path

import fitz
import pytest

from pdf_modifier.interfaces.mcp import (
    extract_embedded_fonts,
    inspect_pdf_fonts,
)

# System font available on Windows (CI is Linux, so we skip font-embedding tests)
_SYSTEM_FONT = None
for _candidate in ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/times.ttf"):
    if os.path.exists(_candidate):
        _SYSTEM_FONT = _candidate
        break


def _get_system_font(tmp_path: Path) -> Path:
    """Copy a real system font into tmp_path so PyMuPDF can embed it."""
    if _SYSTEM_FONT is None:
        pytest.skip("No system font available (not running on Windows)")
    assert _SYSTEM_FONT is not None
    dest = tmp_path / "arial.ttf"
    dest.write_bytes(Path(_SYSTEM_FONT).read_bytes())
    return dest


class TestExtractEmbeddedFonts:
    """Tests for extract_embedded_fonts MCP tool."""

    def _create_pdf_with_custom_font(self, tmp_path: Path) -> Path:
        """Create a PDF with an embedded custom font."""
        font_file = _get_system_font(tmp_path)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "Hello Custom Font",
            fontname="myfont",
            fontfile=str(font_file),
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

    def test_tool_exists(self) -> None:
        """extract_embedded_fonts is callable and registered."""
        # The tool is registered via @mcp.tool() decorator.
        # Verify it's callable by checking the function exists.
        from pdf_modifier.interfaces.mcp import extract_embedded_fonts

        assert callable(extract_embedded_fonts)

    def test_returns_json(self, tmp_path: Path) -> None:
        """Tool returns valid JSON."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        result = extract_embedded_fonts(str(pdf_path))
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_returns_fonts(self, tmp_path: Path) -> None:
        """Tool returns embedded fonts from a PDF with custom fonts."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        result = extract_embedded_fonts(str(pdf_path))
        parsed = json.loads(result)
        assert parsed.get("success") is True
        assert len(parsed.get("fonts", [])) >= 1

    def test_returns_empty_for_base14(self, tmp_path: Path) -> None:
        """Tool returns empty fonts list for Base 14 only PDF."""
        pdf_path = self._create_pdf_with_base14_only(tmp_path)
        result = extract_embedded_fonts(str(pdf_path))
        parsed = json.loads(result)
        assert parsed.get("success") is True
        assert len(parsed.get("fonts", [])) == 0

    def test_font_fields_present(self, tmp_path: Path) -> None:
        """Each font entry has required fields."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        result = extract_embedded_fonts(str(pdf_path))
        parsed = json.loads(result)
        fonts = parsed.get("fonts", [])
        assert len(fonts) >= 1
        for font in fonts:
            assert "name" in font
            assert "type" in font
            assert "subtype" in font
            assert "buffer_size" in font
            assert "page_numbers" in font

    def test_buffer_size_positive(self, tmp_path: Path) -> None:
        """Buffer sizes are positive for embedded fonts."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        result = extract_embedded_fonts(str(pdf_path))
        parsed = json.loads(result)
        for font in parsed.get("fonts", []):
            assert font["buffer_size"] > 0

    def test_tool_invalid_file(self, tmp_path: Path) -> None:
        """Tool returns error for non-existent file."""
        result = extract_embedded_fonts(str(tmp_path / "missing.pdf"))
        parsed = json.loads(result)
        assert parsed.get("success") is False


class TestInspectFontsEnhanced:
    """Tests for enhanced inspect_pdf_fonts with embedded font info."""

    def _create_pdf_with_custom_font(self, tmp_path: Path) -> Path:
        """Create a PDF with an embedded custom font containing searchable text."""
        font_file = _get_system_font(tmp_path)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "Custom Font Text",
            fontname="myfont",
            fontfile=str(font_file),
            fontsize=12,
        )
        pdf_path = tmp_path / "custom_font.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_inspect_fonts_still_works(self, tmp_path: Path) -> None:
        """Existing inspect_fonts behavior is preserved."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        result = inspect_pdf_fonts(str(pdf_path), ["Custom"])
        parsed = json.loads(result)
        assert parsed.get("success") is True
        assert parsed.get("total_matches", 0) >= 1

    def test_inspect_fonts_no_match(self, tmp_path: Path) -> None:
        """inspect_fonts returns no matches for non-existent term."""
        pdf_path = self._create_pdf_with_custom_font(tmp_path)
        result = inspect_pdf_fonts(str(pdf_path), ["NonExistentTerm123"])
        parsed = json.loads(result)
        assert parsed.get("success") is True
        assert parsed.get("total_matches", 0) == 0
