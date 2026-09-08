"""Tests for the whole-span exact match option (CORE-146).

`whole_span=True` requires a target to match the ENTIRE span text instead of
a substring, preventing short targets from corrupting neighbouring content
(e.g. target ``24`` mangling ``24 hours``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz

from pdf_modifier.core import PDFModifier
from pdf_modifier.core.models import ReplacementSpec

from ...conftest import create_pdf

if TYPE_CHECKING:
    from pathlib import Path


def _page_text(path: Path) -> str:
    doc = fitz.open(str(path))
    text = doc[0].get_text()
    doc.close()
    return text


class TestWholeSpanLiteral:
    """Literal targets under whole_span must match the full span text only."""

    def test_whole_span_rejects_partial_substring(self, tmp_path: Path) -> None:
        """Target 24 does not replace a span containing 24 hours."""
        pdf_path = create_pdf(tmp_path / "in.pdf", text="24 hours")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"24": "X"}, whole_span=True)
        result = modifier.process(spec)
        assert result.replacements_made == 0
        assert "24 hours" in _page_text(output)
        assert "X" not in _page_text(output)

    def test_whole_span_matches_exact_span(self, tmp_path: Path) -> None:
        """Target 24 replaces a span whose full text is exactly 24."""
        pdf_path = tmp_path / "in.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "24", fontsize=12)
        page.insert_text((100, 200), "24 hours", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"24": "25"}, whole_span=True)
        result = modifier.process(spec)

        assert result.replacements_made == 1
        text = _page_text(output)
        assert "25" in text
        assert "24 hours" in text

    def test_default_substring_behaviour_unchanged(self, tmp_path: Path) -> None:
        """With whole_span=False (default), 24 still substring-matches 24 hours."""
        pdf_path = create_pdf(tmp_path / "in.pdf", text="24 hours")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"24": "X"})
        result = modifier.process(spec)
        assert result.replacements_made == 1

    def test_whole_span_matches_after_strip(self, tmp_path: Path) -> None:
        """Span text is stripped before the equality check, like the old path."""
        pdf_path = tmp_path / "in.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "24 ", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"24": "25"}, whole_span=True)
        result = modifier.process(spec)
        assert result.replacements_made == 1


class TestWholeSpanRegex:
    """whole_span + use_regex switches the regex match to fullmatch."""

    def test_regex_fullmatch_rejects_partial(self, tmp_path: Path) -> None:
        pdf_path = create_pdf(tmp_path / "in.pdf", text="24 hours")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"24": "X"}, use_regex=True, whole_span=True)
        result = modifier.process(spec)
        assert result.replacements_made == 0
        assert "24 hours" in _page_text(output)

    def test_regex_fullmatch_matches_exact(self, tmp_path: Path) -> None:
        pdf_path = create_pdf(tmp_path / "in.pdf", text="24")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"24": "X"}, use_regex=True, whole_span=True)
        result = modifier.process(spec)
        assert result.replacements_made == 1


class TestWholeSpanCrossSpan:
    """Cross-span matching respects whole_span via exact concatenation."""

    def _two_span_pdf(self, tmp_path: Path) -> Path:
        """PDF with two adjacent spans forming 'Hello World'."""
        pdf_path = tmp_path / "in.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Hello ", fontsize=12, fontname="helv")
        page.insert_text((140, 100), "World", fontsize=12, fontname="cour")
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_cross_span_exact_concatenation_matches(self, tmp_path: Path) -> None:
        """'Hello World' spanning two spans matches when whole_span=True."""
        pdf_path = self._two_span_pdf(tmp_path)
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello World": "Goodbye World"}, whole_span=True)
        result = modifier.process(spec)
        assert result.replacements_made >= 1

    def test_cross_span_partial_target_rejected(self, tmp_path: Path) -> None:
        """A target that is a substring of the concatenation but equals no
        individual span does not match under whole_span."""
        pdf_path = self._two_span_pdf(tmp_path)
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"o Wo": "X"}, whole_span=True)
        result = modifier.process(spec)
        assert result.replacements_made == 0
        assert "o Wo" in _page_text(output)
