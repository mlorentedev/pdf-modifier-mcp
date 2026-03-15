"""Tests for file size validation in PDFAnalyzer and PDFModifier."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from pdf_modifier_mcp.core.analyzer import PDFAnalyzer
from pdf_modifier_mcp.core.exceptions import FileSizeExceededError, PDFNotFoundError
from pdf_modifier_mcp.core.models import ReplacementSpec
from pdf_modifier_mcp.core.modifier import PDFModifier
from tests.conftest import create_pdf


class TestAnalyzerFileSizeValidation:
    """File size validation for PDFAnalyzer."""

    def test_rejects_file_exceeding_max_size(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        # Set limit to 1 byte so any real PDF exceeds it
        analyzer = PDFAnalyzer(pdf, max_file_size=1)
        with pytest.raises(FileSizeExceededError, match="exceeds limit"):
            analyzer.get_structure()

    def test_accepts_file_within_limit(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        # 10 MB limit — small test PDF is well within
        analyzer = PDFAnalyzer(pdf, max_file_size=10 * 1024 * 1024)
        result = analyzer.get_structure()
        assert result.success is True

    def test_error_includes_file_details(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        analyzer = PDFAnalyzer(pdf, max_file_size=1)
        with pytest.raises(FileSizeExceededError) as exc_info:
            analyzer.extract_text()
        assert exc_info.value.details["path"] == str(pdf)
        assert exc_info.value.details["size_bytes"] > 0
        assert exc_info.value.details["limit_bytes"] == 1

    def test_default_limit_allows_normal_pdf(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        # Default 100 MB limit
        analyzer = PDFAnalyzer(pdf)
        result = analyzer.get_structure()
        assert result.success is True

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer(tmp_path / "nonexistent.pdf")
        with pytest.raises(PDFNotFoundError, match="not found"):
            analyzer.get_structure()

    def test_all_methods_validate_size(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        analyzer = PDFAnalyzer(pdf, max_file_size=1)

        with pytest.raises(FileSizeExceededError):
            analyzer.get_structure()

        with pytest.raises(FileSizeExceededError):
            analyzer.extract_text()

        with pytest.raises(FileSizeExceededError):
            analyzer.inspect_fonts(["test"])

        with pytest.raises(FileSizeExceededError):
            analyzer.get_hyperlinks()


class TestModifierFileSizeValidation:
    """File size validation for PDFModifier."""

    def test_rejects_file_exceeding_max_size(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output = tmp_path / "output.pdf"
        modifier = PDFModifier(pdf, output, max_file_size=1)
        spec = ReplacementSpec(replacements={"Hello": "World"})
        with pytest.raises(FileSizeExceededError, match="exceeds limit"):
            modifier.process(spec)

    def test_accepts_file_within_limit(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf", text="Hello World")
        output = tmp_path / "output.pdf"
        modifier = PDFModifier(pdf, output, max_file_size=10 * 1024 * 1024)
        spec = ReplacementSpec(replacements={"Hello": "Hola"})
        result = modifier.process(spec)
        assert result.success is True

    def test_error_includes_file_details(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output = tmp_path / "output.pdf"
        modifier = PDFModifier(pdf, output, max_file_size=1)
        spec = ReplacementSpec(replacements={"Hello": "World"})
        with pytest.raises(FileSizeExceededError) as exc_info:
            modifier.process(spec)
        assert exc_info.value.details["path"] == str(pdf)
        assert exc_info.value.details["size_bytes"] > 0
        assert exc_info.value.details["limit_bytes"] == 1

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        output = tmp_path / "output.pdf"
        modifier = PDFModifier(tmp_path / "nonexistent.pdf", output)
        spec = ReplacementSpec(replacements={"Hello": "World"})
        with pytest.raises(PDFNotFoundError, match="not found"):
            modifier.process(spec)

    def test_context_manager_validates_size(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf")
        output = tmp_path / "output.pdf"
        modifier = PDFModifier(pdf, output, max_file_size=1)
        with pytest.raises(FileSizeExceededError), modifier:
            spec = ReplacementSpec(replacements={"Hello": "World"})
            modifier.process(spec)

    def test_default_limit_allows_normal_pdf(self, tmp_path: Path) -> None:
        pdf = create_pdf(tmp_path / "input.pdf", text="Hello World")
        output = tmp_path / "output.pdf"
        modifier = PDFModifier(pdf, output)
        spec = ReplacementSpec(replacements={"Hello": "Hola"})
        result = modifier.process(spec)
        assert result.success is True
