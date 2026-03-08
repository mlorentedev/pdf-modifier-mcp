"""Tests for hyperlink extraction."""

from pathlib import Path

import fitz

from pdf_modifier_mcp.core import PDFAnalyzer
from pdf_modifier_mcp.core.models import HyperlinkInventory


def test_get_hyperlinks(tmp_path: Path) -> None:
    # Create a PDF with a link
    pdf_path = tmp_path / "test_links.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Google")

    # Add a link over the text area
    link_rect = fitz.Rect(95, 90, 150, 110)
    page.insert_link({"from": link_rect, "uri": "https://google.com", "kind": fitz.LINK_URI})

    doc.save(str(pdf_path))
    doc.close()

    # Analyze it
    analyzer = PDFAnalyzer(pdf_path)
    inventory = analyzer.get_hyperlinks()

    assert isinstance(inventory, HyperlinkInventory)
    assert inventory.total_links == 1
    assert inventory.links[0].uri == "https://google.com"
    assert inventory.links[0].text is not None
    assert "Google" in inventory.links[0].text
    assert inventory.links[0].page == 1


def test_get_hyperlinks_no_links(tmp_path: Path) -> None:
    # Create a PDF without links
    pdf_path = tmp_path / "no_links.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    analyzer = PDFAnalyzer(pdf_path)
    inventory = analyzer.get_hyperlinks()

    assert inventory.total_links == 0
    assert len(inventory.links) == 0
