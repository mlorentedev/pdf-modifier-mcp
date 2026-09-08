"""Regression tests for metadata preservation on text replacement.

A faithful replica must not silently rewrite the PDF's identity metadata
(creationDate, modDate, producer, …). By default the modifier preserves the
original metadata; ``preserve_metadata=False`` opts into stamping a fresh
``modDate`` to reflect the edit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz

from pdf_modifier.core.models import ReplacementSpec
from pdf_modifier.core.modifier import PDFModifier

if TYPE_CHECKING:
    from pathlib import Path

_META = {
    "title": "My Title",
    "author": "An Author",
    "subject": "A Subject",
    "keywords": "some,keywords",
    "creator": "Test Creator",
    "producer": "Original Producer",
    "creationDate": "D:20200101000000+00'00'",
    "modDate": "D:20200101000000+00'00'",
}


def _create_pdf_with_metadata(tmp_path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "HELLO", fontname="helv", fontsize=12)
    doc.set_metadata(dict(_META))
    pdf_path = tmp_path / "meta.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def _output_metadata(path: Path) -> dict[str, str]:
    d = fitz.open(str(path))
    md = dict(d.metadata)
    d.close()
    return md


class TestModifierMetadataPreservation:
    """metadata should be preserved on replacement by default."""

    def test_metadata_preserved_by_default(self, tmp_path: Path) -> None:
        src = _create_pdf_with_metadata(tmp_path)
        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={"HELLO": "HI"}))

        md = _output_metadata(out)
        for key, expected in _META.items():
            assert md.get(key) == expected, f"metadata[{key!r}] changed: {md.get(key)!r}"

    def test_creation_and_mod_date_preserved(self, tmp_path: Path) -> None:
        src = _create_pdf_with_metadata(tmp_path)
        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={"HELLO": "HI"}))
        md = _output_metadata(out)
        assert md["creationDate"] == "D:20200101000000+00'00'"
        assert md["modDate"] == "D:20200101000000+00'00'"

    def test_text_still_replaced(self, tmp_path: Path) -> None:
        src = _create_pdf_with_metadata(tmp_path)
        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={"HELLO": "HI"}))
        d = fitz.open(str(out))
        text = d[0].get_text("text")
        d.close()
        assert "HI" in text
        assert "HELLO" not in text

    def test_disable_allows_mod_date_change(self, tmp_path: Path) -> None:
        src = _create_pdf_with_metadata(tmp_path)
        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out), preserve_metadata=False).process(
            ReplacementSpec(replacements={"HELLO": "HI"})
        )
        md = _output_metadata(out)
        assert md["modDate"] != _META["modDate"], "modDate should update when disabled"

    def test_no_metadata_added_when_absent(self, tmp_path: Path) -> None:
        """Preserving must not *inject* metadata that did not exist.

        A source PDF with only a ``title`` (no dates/producer/creator) must stay
        that way after replacement — the engine must not stamp phantom dates or
        a producer. Only the opt-out (``preserve_metadata=False``) may add
        a ``modDate``.
        """
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "HELLO", fontname="helv", fontsize=12)
        doc.set_metadata({"title": "Only Title"})
        src = tmp_path / "partial.pdf"
        doc.save(str(src))
        doc.close()

        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(ReplacementSpec(replacements={"HELLO": "HI"}))
        md = _output_metadata(out)
        # No phantom metadata is injected by default.
        assert md.get("title") == "Only Title"
        assert md.get("creationDate") == ""
        assert md.get("modDate") == ""
        assert md.get("producer") == ""
        assert md.get("creator") == ""


class TestModifierMetadataValidation:
    """The flag is a boolean and defaults to preserving."""

    def test_default_is_true(self) -> None:
        m = PDFModifier("a.pdf", "b.pdf")
        assert m.preserve_metadata is True
