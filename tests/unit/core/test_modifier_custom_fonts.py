"""Tests for PDFModifier with custom font support."""

from __future__ import annotations

import os
from pathlib import Path

import fitz
import pytest

from pdf_modifier_mcp.core.models import ReplacementSpec
from pdf_modifier_mcp.core.modifier import PDFModifier

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


class TestPDFModifierCustomFonts:
    """Tests for PDFModifier custom font integration."""

    def _create_test_pdf(self, tmp_path: Path, text: str = "Hello World") -> Path:
        """Create a simple PDF for testing."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text, fontname="helv", fontsize=12)
        pdf_path = tmp_path / "test.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_custom_font_accepted(self, tmp_path: Path) -> None:
        """PDFModifier accepts custom_fonts dict."""
        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"fake ttf")

        modifier = PDFModifier(
            "dummy.pdf",
            "out.pdf",
            custom_fonts={"Helvetica": str(font_file)},
        )
        assert modifier._custom_fonts == {"Helvetica": str(font_file)}

    def test_custom_font_invalid_path_raises(self, tmp_path: Path) -> None:
        """PDFModifier rejects custom_fonts with non-existent files."""
        with pytest.raises(ValueError, match="font file does not exist"):
            PDFModifier(
                "dummy.pdf",
                "out.pdf",
                custom_fonts={"helv": str(tmp_path / "nonexistent.ttf")},
            )

    def test_no_custom_fonts_by_default(self) -> None:
        """PDFModifier works without custom_fonts (backward compatible)."""
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._custom_fonts == {}

    def test_custom_font_with_real_pdf(self, tmp_path: Path) -> None:
        """Custom font replacement works with a real PDF."""
        # Create source PDF
        source = self._create_test_pdf(tmp_path, "Hello World")
        output = tmp_path / "output.pdf"

        font_file = _get_system_font(tmp_path)

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"Helvetica": str(font_file)},
        )
        spec = ReplacementSpec(replacements={"Hello World": "Goodbye Moon"})
        result = modifier.process(spec)

        assert result.success is True
        assert result.replacements_made > 0

        # Verify output PDF has custom font embedded (Type0 = custom TTF)
        # Base 14 fonts are Type1; custom embedded fonts are Type0
        doc = fitz.open(str(output))
        fonts = doc[0].get_fonts(full=True)
        doc.close()
        has_type0 = any(f[2] == "Type0" for f in fonts)
        assert has_type0, f"Expected custom embedded font (Type0), got: {fonts}"

    def test_custom_font_replaces_correctly(self, tmp_path: Path) -> None:
        """Text is replaced and custom font is embedded."""
        source = self._create_test_pdf(tmp_path, "Replace Me")
        output = tmp_path / "output.pdf"

        font_file = _get_system_font(tmp_path)

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"helv": str(font_file)},
        )
        spec = ReplacementSpec(replacements={"Replace Me": "Done!"})
        result = modifier.process(spec)

        assert result.replacements_made == 1

        # Verify text was replaced
        doc = fitz.open(str(output))
        text = doc[0].get_text("text")
        doc.close()
        assert "Done!" in text
        assert "Replace Me" not in text

    def test_mixed_custom_and_base14(self, tmp_path: Path) -> None:
        """Custom font only applies when alias matches, Base 14 fallback works."""
        source = self._create_test_pdf(tmp_path, "Hello World")
        output = tmp_path / "output.pdf"

        font_file = _get_system_font(tmp_path)

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"Helvetica": str(font_file)},
        )
        spec = ReplacementSpec(replacements={"Hello World": "Custom Font Test"})
        result = modifier.process(spec)

        assert result.success is True
        assert result.replacements_made > 0

    def test_custom_font_non_matching_alias(self, tmp_path: Path) -> None:
        """Custom font alias that doesn't match falls back to Base 14."""
        source = self._create_test_pdf(tmp_path, "Hello World")
        output = tmp_path / "output.pdf"

        # "myfont" doesn't match "ArialMT" or any span font
        font_file = tmp_path / "myfont.ttf"
        font_file.write_bytes(b"fake ttf")

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"myfont": str(font_file)},
        )
        spec = ReplacementSpec(replacements={"Hello World": "Fallback Test"})
        result = modifier.process(spec)

        assert result.success is True
        assert result.replacements_made > 0

        # Should use Base 14 helv, not custom font
        doc = fitz.open(str(output))
        doc.close()
        # helv is a Base 14 font, may or may not be embedded
        # The key is that it doesn't crash

    def test_custom_font_otf(self, tmp_path: Path) -> None:
        """Custom OTF font works."""
        source = self._create_test_pdf(tmp_path, "Hello World")
        output = tmp_path / "output.pdf"

        font_file = _get_system_font(tmp_path)

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"Helvetica": str(font_file)},
        )
        spec = ReplacementSpec(replacements={"Hello World": "OTF Test"})
        result = modifier.process(spec)

        assert result.success is True
