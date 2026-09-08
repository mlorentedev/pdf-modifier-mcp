"""Regression test: a text replacement must not bloat the output file.

``doc.save()`` with the default options leaves unused objects (old font
resources, superseded streams) in the output, which grew a 67 kB PDF to ~94 kB
(+46%). Saving with ``garbage=4`` + ``deflate`` removes them, keeping the output
at the original size. This guards against a regression to the bloated save.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz

from pdf_modifier.core.models import ReplacementSpec
from pdf_modifier.core.modifier import PDFModifier

if TYPE_CHECKING:
    from pathlib import Path


def _create_multipage_pdf(tmp_path: Path) -> Path:
    doc = fitz.open()
    for i in range(15):
        page = doc.new_page()
        page.insert_text(
            (50, 60), f"Content line {i} for the size test", fontname="helv", fontsize=9
        )
    pdf_path = tmp_path / "src.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


class TestModifierOutputSize:
    """Replacing text should not significantly grow the file."""

    def test_output_not_bloated(self, tmp_path: Path) -> None:
        src = _create_multipage_pdf(tmp_path)
        orig_size = src.stat().st_size

        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={"test": "TEST"}, use_regex=True)
        )
        out_size = out.stat().st_size

        # With garbage+deflate the output stays ~= input. Without it a simple
        # replacement grows the file by 7%+ (and far more on embedded-font PDFs).
        assert out_size <= int(orig_size * 1.05), (
            f"output grew to {out_size} bytes vs {orig_size} input "
            f"(ratio {out_size / orig_size:.2f}) — save must use garbage/deflate"
        )
