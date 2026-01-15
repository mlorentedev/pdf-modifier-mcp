"""Tests for PDFAnalyzer."""

from pathlib import Path

import pytest

from pdf_modifier_mcp.core import PDFAnalyzer
from pdf_modifier_mcp.core.exceptions import PDFReadError
from pdf_modifier_mcp.core.models import FontInspectionResult, PDFStructure

from ...conftest import SAMPLE_PDF


class TestPDFAnalyzer:
    """Tests for PDFAnalyzer."""

    def test_init_with_string_path(self) -> None:
        analyzer = PDFAnalyzer(str(SAMPLE_PDF))
        assert analyzer.file_path == SAMPLE_PDF

    def test_init_with_path_object(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        assert analyzer.file_path == SAMPLE_PDF

    def test_get_structure_returns_pdf_structure(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        structure = analyzer.get_structure()
        assert isinstance(structure, PDFStructure)
        assert structure.total_pages >= 1

    def test_get_structure_contains_elements(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        structure = analyzer.get_structure()
        has_elements = any(len(page.elements) > 0 for page in structure.pages)
        assert has_elements

    def test_get_structure_raises_on_invalid_file(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer(tmp_path / "nonexistent.pdf")
        with pytest.raises(PDFReadError):
            analyzer.get_structure()

    def test_extract_text_returns_string(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        text = analyzer.extract_text()
        assert isinstance(text, str)
        assert "--- Page 1 ---" in text

    def test_extract_text_raises_on_invalid_file(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer(tmp_path / "nonexistent.pdf")
        with pytest.raises(PDFReadError):
            analyzer.extract_text()

    def test_inspect_fonts_returns_result(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        result = analyzer.inspect_fonts(["Order"])
        assert isinstance(result, FontInspectionResult)
        assert result.total_matches >= 0

    def test_inspect_fonts_no_matches(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        result = analyzer.inspect_fonts(["XYZNONEXISTENT123"])
        assert result.total_matches == 0
