"""Unit tests for core modules: modifier, analyzer, exceptions."""

from pathlib import Path

import pytest

from pdf_modifier_mcp.core import PDFAnalyzer, PDFModifier
from pdf_modifier_mcp.core.exceptions import (
    FileSizeError,
    InvalidPatternError,
    PDFModifierError,
    PDFNotFoundError,
    PDFReadError,
    PDFWriteError,
    TextNotFoundError,
)
from pdf_modifier_mcp.core.models import FontInspectionResult, PDFStructure

TEST_DATA_DIR = Path(__file__).parent / "data"
SAMPLE_PDF = TEST_DATA_DIR / "sample.pdf"


# =============================================================================
# PDFModifier Tests
# =============================================================================
class TestPDFModifier:
    """Tests for PDFModifier internal methods."""

    def test_get_font_properties_helvetica(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("ArialMT")
        assert code == "helv"
        assert name == "Helvetica"

    def test_get_font_properties_bold(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("Arial-BoldMT")
        assert code == "HeBo"
        assert name == "Helvetica-Bold"

    def test_get_font_properties_courier(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("CourierNew")
        assert code == "Cour"
        assert name == "Courier"

    def test_convert_color_int(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color(16711680)  # Red: 0xFF0000
        assert (r, g, b) == (1.0, 0.0, 0.0)

    def test_convert_color_tuple(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color((0.5, 0.5, 0.5))
        assert (r, g, b) == (0.5, 0.5, 0.5)

    def test_convert_color_invalid(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color("invalid")  # type: ignore[arg-type]
        assert (r, g, b) == (0.0, 0.0, 0.0)


# =============================================================================
# PDFAnalyzer Tests
# =============================================================================
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


# =============================================================================
# Exception Tests
# =============================================================================
class TestExceptions:
    """Tests for custom exceptions."""

    def test_base_error_initialization(self) -> None:
        error = PDFModifierError("Test message", {"key": "value"})
        assert error.message == "Test message"
        assert error.details == {"key": "value"}

    def test_base_error_to_dict(self) -> None:
        error = PDFModifierError("Test error")
        result = error.to_dict()
        assert result["success"] is False
        assert result["error"] == "PDF_ERROR"
        assert result["message"] == "Test error"

    def test_error_codes(self) -> None:
        assert PDFNotFoundError("x").code == "FILE_NOT_FOUND"
        assert PDFReadError("x").code == "READ_ERROR"
        assert PDFWriteError("x").code == "WRITE_ERROR"
        assert InvalidPatternError("x").code == "INVALID_PATTERN"
        assert TextNotFoundError("x").code == "TEXT_NOT_FOUND"
        assert FileSizeError("x").code == "FILE_TOO_LARGE"

    def test_all_inherit_from_base(self) -> None:
        exceptions = [
            PDFNotFoundError,
            PDFReadError,
            PDFWriteError,
            InvalidPatternError,
            TextNotFoundError,
            FileSizeError,
        ]
        for exc_class in exceptions:
            assert isinstance(exc_class("Test"), PDFModifierError)

    def test_can_catch_with_base_class(self) -> None:
        with pytest.raises(PDFModifierError):
            raise PDFReadError("Test")
