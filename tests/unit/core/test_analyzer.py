"""Tests for PDFAnalyzer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz
import pytest

from pdf_modifier_mcp.core import PDFAnalyzer
from pdf_modifier_mcp.core.exceptions import PDFNotFoundError, PDFPasswordError
from pdf_modifier_mcp.core.models import FontInspectionResult, HyperlinkInventory, PDFStructure

from ...conftest import SAMPLE_PDF, create_encrypted_pdf

if TYPE_CHECKING:
    from pathlib import Path


class TestPDFAnalyzerInit:
    """Tests for PDFAnalyzer initialization."""

    def test_init_with_string_path(self) -> None:
        analyzer = PDFAnalyzer(str(SAMPLE_PDF))
        assert analyzer.file_path == SAMPLE_PDF

    def test_init_with_path_object(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        assert analyzer.file_path == SAMPLE_PDF


class TestGetStructure:
    """Tests for get_structure method."""

    def test_returns_pdf_structure(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        structure = analyzer.get_structure()
        assert isinstance(structure, PDFStructure)
        assert structure.total_pages >= 1

    def test_contains_elements(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        structure = analyzer.get_structure()
        has_elements = any(len(page.elements) > 0 for page in structure.pages)
        assert has_elements

    def test_page_dimensions_positive(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        structure = analyzer.get_structure()
        for page in structure.pages:
            assert page.width > 0
            assert page.height > 0

    def test_text_elements_have_properties(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        structure = analyzer.get_structure()
        elements = [e for p in structure.pages for e in p.elements if e.text.strip()]
        assert len(elements) > 0
        elem = elements[0]
        assert elem.font
        assert elem.size > 0
        assert len(elem.bbox) == 4
        assert len(elem.origin) == 2

    def test_raises_on_invalid_file(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer(tmp_path / "nonexistent.pdf")
        with pytest.raises(PDFNotFoundError):
            analyzer.get_structure()


class TestExtractText:
    """Tests for extract_text method."""

    def test_returns_string(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        text = analyzer.extract_text()
        assert isinstance(text, str)
        assert "--- Page 1 ---" in text

    def test_raises_on_invalid_file(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer(tmp_path / "nonexistent.pdf")
        with pytest.raises(PDFNotFoundError):
            analyzer.extract_text()

    def test_multipage_text_extraction(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "multi.pdf"
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((100, 100), f"Page {i + 1} content")
        doc.save(str(pdf_path))
        doc.close()

        analyzer = PDFAnalyzer(pdf_path)
        text = analyzer.extract_text()
        assert "Page 1 content" in text
        assert "Page 2 content" in text
        assert "Page 3 content" in text
        assert "3 pages" in text


class TestInspectFonts:
    """Tests for inspect_fonts method."""

    def test_returns_result(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        result = analyzer.inspect_fonts(["Order"])
        assert isinstance(result, FontInspectionResult)
        assert result.total_matches >= 0

    def test_no_matches(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        result = analyzer.inspect_fonts(["XYZNONEXISTENT123"])
        assert result.total_matches == 0

    def test_multiple_terms(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        result = analyzer.inspect_fonts(["Order", "$"])
        assert result.terms_searched == ["Order", "$"]

    def test_match_contains_font_info(self) -> None:
        analyzer = PDFAnalyzer(SAMPLE_PDF)
        result = analyzer.inspect_fonts(["Order"])
        if result.total_matches > 0:
            match = result.matches[0]
            assert match.font
            assert match.size > 0
            assert match.page >= 1


class TestGetHyperlinks:
    """Tests for get_hyperlinks method."""

    def test_pdf_with_no_links(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "no_links.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        analyzer = PDFAnalyzer(pdf_path)
        result = analyzer.get_hyperlinks()
        assert isinstance(result, HyperlinkInventory)
        assert result.total_links == 0

    def test_raises_on_invalid_file(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer(tmp_path / "missing.pdf")
        with pytest.raises(PDFNotFoundError):
            analyzer.get_hyperlinks()


class TestEncryptedPDFAnalysis:
    """Tests for analyzing encrypted PDFs."""

    def test_encrypted_without_password_raises(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(tmp_path / "encrypted.pdf")
        analyzer = PDFAnalyzer(pdf_path)
        with pytest.raises(PDFPasswordError, match="password protected"):
            analyzer.get_structure()

    def test_encrypted_wrong_password_raises(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(
            tmp_path / "encrypted.pdf", user_pw="right", owner_pw="owner"
        )
        analyzer = PDFAnalyzer(pdf_path, password="wrong")
        with pytest.raises(PDFPasswordError, match="Incorrect password"):
            analyzer.get_structure()

    def test_encrypted_correct_password_works(self, tmp_path: Path) -> None:
        full_perm = int(
            fitz.PDF_PERM_ACCESSIBILITY
            | fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
        )
        pdf_path = create_encrypted_pdf(
            tmp_path / "encrypted.pdf",
            user_pw="right",
            owner_pw="owner",
            permissions=full_perm,
        )
        analyzer = PDFAnalyzer(pdf_path, password="right")
        structure = analyzer.get_structure()
        assert structure.total_pages == 1

    def test_extract_text_encrypted_without_password(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(tmp_path / "encrypted.pdf", user_pw="pass123")
        analyzer = PDFAnalyzer(pdf_path)
        with pytest.raises(PDFPasswordError):
            analyzer.extract_text()

    def test_inspect_fonts_encrypted_without_password(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(tmp_path / "encrypted.pdf", user_pw="pass123")
        analyzer = PDFAnalyzer(pdf_path)
        with pytest.raises(PDFPasswordError):
            analyzer.inspect_fonts(["Secret"])
