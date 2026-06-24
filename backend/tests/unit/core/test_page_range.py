"""Tests for page range filtering in PDFModifier."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import fitz
import pytest

from pdf_modifier.core import PDFModifier
from pdf_modifier.core.models import ReplacementSpec

from ...conftest import create_pdf


def _create_multi_page_pdf(tmp_path: Path, texts: list[str]) -> Path:
    """Helper: create a multi-page PDF with given text per page."""
    doc = fitz.open()
    for text in texts:
        page = doc.new_page()
        page.insert_text((100, 100), text)
    path = tmp_path / "multi.pdf"
    doc.save(str(path))
    doc.close()
    return path


class TestPageRangeSinglePage:
    """Page range on single-page PDFs."""

    def test_page_range_single_page(self, tmp_path: Path) -> None:
        """Specifying page 1 on a 1-page PDF processes it."""
        pdf_path = create_pdf(tmp_path / "one.pdf", text="Hello World")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = modifier.process(spec, pages=(1, 1))
        assert result.success
        assert result.replacements_made == 1
        assert result.pages_modified == 1

    def test_page_range_out_of_bounds_raises(self, tmp_path: Path) -> None:
        """Page range exceeding total pages raises ValueError."""
        pdf_path = create_pdf(tmp_path / "one.pdf", text="Hello World")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        with pytest.raises(ValueError, match="Page 2 exceeds"):
            modifier.process(spec, pages=(1, 2))

    def test_page_range_zero_raises(self, tmp_path: Path) -> None:
        """Page range starting at 0 raises ValueError (1-indexed)."""
        pdf_path = create_pdf(tmp_path / "one.pdf", text="Hello World")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        with pytest.raises(ValueError, match="Page numbers must be 1-indexed"):
            modifier.process(spec, pages=(0, 1))

    def test_page_range_negative_raises(self, tmp_path: Path) -> None:
        """Negative page numbers raise ValueError."""
        pdf_path = create_pdf(tmp_path / "one.pdf", text="Hello World")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        with pytest.raises(ValueError, match="Page numbers must be 1-indexed"):
            modifier.process(spec, pages=(-1, 1))


class TestPageRangeMultiPage:
    """Page range on multi-page PDFs."""

    def test_page_range_first_page_only(self, tmp_path: Path) -> None:
        """Range (1, 1) processes only the first page."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["Hello World", "Foo Bar"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = modifier.process(spec, pages=(1, 1))
        assert result.success
        assert result.replacements_made == 1
        assert result.pages_modified == 1

    def test_page_range_middle_pages(self, tmp_path: Path) -> None:
        """Range (2, 3) processes only pages 2 and 3."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["A", "B", "C", "D"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"B": "b", "C": "c"})
        result = modifier.process(spec, pages=(2, 3))
        assert result.success
        assert result.replacements_made == 2
        assert result.pages_modified == 2

    def test_page_range_skips_unmatched_pages(self, tmp_path: Path) -> None:
        """Pages outside the range are not touched."""
        pdf_path = _create_multi_page_pdf(
            tmp_path,
            ["Hello World", "Foo Bar", "Baz Qux"],
        )
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        result = modifier.process(spec, pages=(1, 1))
        assert result.success
        assert result.replacements_made == 1
        assert result.pages_modified == 1

    def test_page_range_all_pages(self, tmp_path: Path) -> None:
        """Range (1, N) processes all pages."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["Hello World", "Foo Bar"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye", "Foo": "Bar"})
        result = modifier.process(spec, pages=(1, 2))
        assert result.success
        assert result.replacements_made == 2
        assert result.pages_modified == 2

    def test_page_range_no_match_in_range(self, tmp_path: Path) -> None:
        """Range where no text matches produces zero replacements."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["Hello World", "Foo Bar"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"NONEXISTENT": "replacement"})
        result = modifier.process(spec, pages=(1, 2))
        assert result.success
        assert result.replacements_made == 0
        assert result.pages_modified == 0

    def test_page_range_out_of_bounds_raises_multi(self, tmp_path: Path) -> None:
        """Range exceeding total pages raises ValueError."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["A", "B", "C"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"A": "a"})
        with pytest.raises(ValueError, match="Page 5 exceeds"):
            modifier.process(spec, pages=(1, 5))


class TestPageRangeNone:
    """None pages = process all (default behavior)."""

    def test_pages_none_processes_all(self, tmp_path: Path) -> None:
        """pages=None processes all pages (default)."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["Hello World", "Foo Bar"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye", "Foo": "Bar"})
        result = modifier.process(spec, pages=None)
        assert result.success
        assert result.replacements_made == 2
        assert result.pages_modified == 2

    def test_pages_not_specified_processes_all(self, tmp_path: Path) -> None:
        """Omitting pages parameter processes all pages."""
        pdf_path = _create_multi_page_pdf(tmp_path, ["Hello World", "Foo Bar"])
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye", "Foo": "Bar"})
        result = modifier.process(spec)
        assert result.success
        assert result.replacements_made == 2
        assert result.pages_modified == 2


class TestPageRangeEmptyRange:
    """Edge cases for empty or invalid ranges."""

    def test_reverse_range_raises(self, tmp_path: Path) -> None:
        """Start > end raises ValueError."""
        pdf_path = create_pdf(tmp_path / "one.pdf", text="Hello World")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
        with pytest.raises(ValueError, match="start must not exceed"):
            modifier.process(spec, pages=(3, 1))
