"""Regression test for preserving a vector-drawn background on replacement.

Reproduces the bug where ``add_redact_annot(..., fill=(1, 1, 1))`` paints a
white box over the surrounding PDF content (e.g. a colored invoice band),
instead of preserving it. The fix uses ``fill=None`` so the underlying vector
drawing stays visible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import fitz

from pdf_modifier.core.models import ReplacementSpec
from pdf_modifier.core.modifier import PDFModifier

if TYPE_CHECKING:
    from pathlib import Path

# Background fill used by the test page (light gray-blue, like an invoice band).
_BG = (0.949, 0.9569, 0.9647)


def _as_rgb255(fill: tuple[float, float, float]) -> tuple[int, int, int]:
    r, g, b = fill
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


_BG255 = _as_rgb255(_BG)


def _create_background_pdf(tmp_path: Path, text: str = "TESTWORD ABC") -> Path:
    """Create a PDF with a filled background rect and text on top."""
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(0, 0, 600, 600), color=None, fill=_BG)
    page.insert_text((72, 72), text, fontname="helv", fontsize=12)
    pdf_path = tmp_path / "bg.pdf"
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def _find_first_background_pixel_in_span(pix: Any) -> tuple[int, int] | None:
    """Return (px_x, px_y) of a non-glyph (background) pixel inside the span."""
    for yy in range(pix.height):
        for xx in range(pix.width):
            px = pix.pixel(xx, yy)
            if (
                abs(px[0] - _BG255[0]) <= 6
                and abs(px[1] - _BG255[1]) <= 6
                and abs(px[2] - _BG255[2]) <= 6
            ):
                return (xx, yy)
    return None


class TestModifierBackgroundPreservation:
    """After replacement, the redacted area keeps the page background."""

    def test_background_not_replaced_with_white(self, tmp_path: Path) -> None:
        src = _create_background_pdf(tmp_path)
        out = tmp_path / "out.pdf"

        # Bounding box of the span we will replace.
        d0 = fitz.open(str(src))
        p0 = d0[0]
        target = None
        for block in p0.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip() == "TESTWORD ABC":
                        target = fitz.Rect(span["bbox"])
        d0.close()
        assert target is not None

        clip = target

        # Baseline: a background pixel exists inside the span (glyph-free spot).
        orig = fitz.open(str(src))[0].get_pixmap(clip=clip, dpi=150)
        bgpix = _find_first_background_pixel_in_span(orig)
        assert bgpix is not None, "no background pixel found inside span bbox"

        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={"TESTWORD ABC": "REPLACED!"})
        )

        d = fitz.open(str(out))
        p = d[0]
        pix = p.get_pixmap(clip=clip, dpi=150)
        got = pix.pixel(*bgpix)
        d.close()

        # Broken behavior paints white (255,255,255). Fixed keeps the background.
        assert got != (255, 255, 255), f"background was replaced with white: {got}"
        assert (
            abs(got[0] - _BG255[0]) <= 8
            and abs(got[1] - _BG255[1]) <= 8
            and abs(got[2] - _BG255[2]) <= 8
        ), f"background was not preserved: got {got}, expected ~{_BG255}"

    def test_replaced_text_present(self, tmp_path: Path) -> None:
        """Text is actually replaced (sanity)."""
        src = _create_background_pdf(tmp_path)
        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={"TESTWORD ABC": "REPLACED!"})
        )
        d = fitz.open(str(out))
        text = d[0].get_text("text")
        d.close()
        assert "REPLACED!" in text
        assert "TESTWORD ABC" not in text


class TestModifierImageBackgroundPreserved:
    """Replacing text that sits on an *image* must not mask/degrade the image.

    The default ``apply_redactions`` options use ``PDF_REDACT_IMAGE_PIXELS``,
    which carves a hole out of the image behind the text. ``images=
    PDF_REDACT_IMAGE_NONE`` preserves it. Regression test for that case.
    """

    _IMG_COLOR = (60, 160, 60)  # opaque green image fill

    def _create_pdf(self, tmp_path: Path, text: str = "TEXT ON IMG") -> Path:
        doc = fitz.open()
        page = doc.new_page()
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 600, 600), 0)
        pix.set_rect(pix.irect, self._IMG_COLOR)
        page.insert_image(fitz.Rect(0, 0, 600, 600), pixmap=pix)
        page.insert_text((72, 72), text, fontname="helv", fontsize=12)
        pdf_path = tmp_path / "img_bg.pdf"
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def _span_bbox(self, path: Path, text: str) -> Any:
        d = fitz.open(str(path))
        target = None
        for block in d[0].get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip() == text:
                        target = fitz.Rect(span["bbox"])
        d.close()
        assert target is not None
        return target

    def _find_interior_green_pixel(self, pix: Any) -> tuple[int, int]:
        for yy in range(pix.height):
            for xx in range(pix.width):
                px = pix.pixel(xx, yy)
                if tuple(px) == self._IMG_COLOR:
                    return (xx, yy)
        raise AssertionError("no interior image pixel found")

    def test_image_background_preserved(self, tmp_path: Path) -> None:
        src = self._create_pdf(tmp_path)
        out = tmp_path / "out.pdf"
        bbox = self._span_bbox(src, "TEXT ON IMG")

        # Locate an interior pixel that is the image color (background, not glyph).
        pix = fitz.open(str(src))[0].get_pixmap(clip=bbox, dpi=150)
        pt = self._find_interior_green_pixel(pix)

        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={"TEXT ON IMG": "NEW"})
        )

        d = fitz.open(str(out))
        p = d[0]
        got = p.get_pixmap(clip=bbox, dpi=150).pixel(*pt)
        d.close()

        # Default behavior masks the image -> white. Fixed keeps the green image.
        assert got != (255, 255, 255), f"image background was masked to white: {got}"
        assert tuple(got) == self._IMG_COLOR, f"image background not preserved: {got}"

    def test_text_removed_on_image(self, tmp_path: Path) -> None:
        """Even with IMAGE_NONE, the original text is still removed."""
        src = self._create_pdf(tmp_path)
        out = tmp_path / "out.pdf"
        PDFModifier(str(src), str(out)).process(
            ReplacementSpec(replacements={"TEXT ON IMG": "NEW"})
        )
        d = fitz.open(str(out))
        text = d[0].get_text("text")
        d.close()
        assert "NEW" in text
        assert "TEXT ON IMG" not in text
