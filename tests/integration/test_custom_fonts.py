"""End-to-end integration test: custom font replacement with real PDF."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import fitz

from pdf_modifier_mcp.core.models import ReplacementSpec
from pdf_modifier_mcp.core.modifier import PDFModifier


class TestCustomFontIntegration:
    """End-to-end test for custom font replacement."""

    def test_full_custom_font_workflow(self, tmp_path: Path) -> None:
        """Create PDF → replace with custom font → verify embedded font + text."""
        # Step 1: Create source PDF with Base 14 font
        source = tmp_path / "source.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello World", fontname="helv", fontsize=14)
        page.insert_text((72, 100), "Goodbye World", fontname="TiRo", fontsize=12)
        doc.save(str(source))
        doc.close()

        # Step 2: Replace with custom font (Arial)
        output = tmp_path / "output.pdf"
        arial_path = "C:/Windows/Fonts/arial.ttf"

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"Helvetica": arial_path, "Times": arial_path},
        )
        spec = ReplacementSpec(
            replacements={
                "Hello World": "Custom Font Test",
                "Goodbye World": "Arial Embedded",
            }
        )
        result = modifier.process(spec)

        # Step 3: Verify replacement succeeded
        assert result.success is True
        assert result.replacements_made >= 2
        assert result.pages_modified >= 1

        # Step 4: Verify text was replaced (PyMuPDF may use \xa0 for spaces)
        doc = fitz.open(str(output))
        text = doc[0].get_text("text").replace("\xa0", " ")
        doc.close()
        assert "Custom Font Test" in text
        assert "Arial Embedded" in text
        assert "Hello World" not in text
        assert "Goodbye World" not in text

        # Step 5: Verify custom font is embedded (Type0 = custom TTF)
        doc = fitz.open(str(output))
        fonts = doc[0].get_fonts(full=True)
        doc.close()
        has_type0 = any(f[2] == "Type0" for f in fonts)
        assert has_type0, f"Expected custom embedded font (Type0), got: {fonts}"

        # Step 6: Verify font extraction works
        from pdf_modifier_mcp.core.analyzer import PDFAnalyzer

        analyzer = PDFAnalyzer(str(output))
        embedded = analyzer.extract_embedded_fonts()
        assert len(embedded) >= 1
        assert all(f.type == "Type0" for f in embedded)
        assert all(len(f.buffer) > 0 for f in embedded)

    def test_custom_font_with_hyperlink(self, tmp_path: Path) -> None:
        """Custom font replacement with hyperlink syntax."""
        source = tmp_path / "source_link.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Click Here", fontname="helv", fontsize=12)
        doc.save(str(source))
        doc.close()

        output = tmp_path / "output_link.pdf"
        arial_path = "C:/Windows/Fonts/arial.ttf"

        modifier = PDFModifier(
            str(source),
            str(output),
            custom_fonts={"Helvetica": arial_path},
        )
        spec = ReplacementSpec(
            replacements={
                "Click Here": "Visit Site|https://example.com",
            }
        )
        result = modifier.process(spec)

        assert result.success is True
        assert result.replacements_made >= 1

        # Verify text and link (PyMuPDF may use \xa0 for spaces)
        doc = fitz.open(str(output))
        text = doc[0].get_text("text").replace("\xa0", " ")
        links = doc[0].get_links()
        doc.close()
        assert "Visit Site" in text
        assert any("example.com" in str(link.get("uri", "")) for link in links)

    def test_no_custom_fonts_backward_compat(self, tmp_path: Path) -> None:
        """PDF without custom_fonts still works (backward compat)."""
        source = tmp_path / "source_compat.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello World", fontname="helv", fontsize=12)
        doc.save(str(source))
        doc.close()

        output = tmp_path / "output_compat.pdf"
        modifier = PDFModifier(str(source), str(output))
        spec = ReplacementSpec(replacements={"Hello World": "Goodbye"})
        result = modifier.process(spec)

        assert result.success is True
        assert result.replacements_made >= 1

        doc = fitz.open(str(output))
        text = doc[0].get_text("text")
        doc.close()
        assert "Goodbye" in text
