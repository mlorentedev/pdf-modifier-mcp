"""Tests for PDFModifier internal methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz
import pytest

from pdf_modifier_mcp.core import PDFModifier
from pdf_modifier_mcp.core.exceptions import PDFPasswordError, PDFReadError
from pdf_modifier_mcp.core.models import ReplacementSpec

from ...conftest import create_encrypted_pdf, create_pdf

if TYPE_CHECKING:
    from pathlib import Path


class TestFontProperties:
    """Tests for font name mapping."""

    def test_helvetica_default(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("ArialMT")
        assert code == "helv"
        assert name == "Helvetica"

    def test_helvetica_bold(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("Arial-BoldMT")
        assert code == "HeBo"
        assert name == "Helvetica-Bold"

    def test_courier(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("CourierNew")
        assert code == "Cour"
        assert name == "Courier"

    def test_courier_bold(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("CourierNew-Bold")
        assert code == "CoBo"
        assert name == "Courier-Bold"

    def test_times(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("TimesNewRomanPSMT")
        assert code == "TiRo"
        assert name == "Times-Roman"

    def test_times_bold(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("TimesNewRoman-Bold")
        assert code == "TiBo"
        assert name == "Times-Bold"

    def test_serif_maps_to_times(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("DejaVuSerif")
        assert code == "TiRo"
        assert name == "Times-Roman"

    def test_unknown_font_defaults_to_helvetica(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        code, name = modifier._get_font_properties("SomeRandomFont")
        assert code == "helv"
        assert name == "Helvetica"


class TestColorConversion:
    """Tests for color input normalization."""

    def test_int_red(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color(0xFF0000) == (1.0, 0.0, 0.0)

    def test_int_green(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color(0x00FF00) == (0.0, 1.0, 0.0)

    def test_int_blue(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color(0x0000FF) == (0.0, 0.0, 1.0)

    def test_int_black(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color(0) == (0.0, 0.0, 0.0)

    def test_float_tuple(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color((0.5, 0.5, 0.5)) == (0.5, 0.5, 0.5)

    def test_float_list(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color([0.1, 0.2, 0.3]) == (0.1, 0.2, 0.3)

    def test_255_scale_normalizes(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        r, g, b = modifier._convert_color([255.0, 128.0, 0.0])
        assert r == 1.0
        assert g == pytest.approx(128.0 / 255.0)
        assert b == 0.0

    def test_invalid_type_returns_black(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color("invalid") == (0.0, 0.0, 0.0)  # type: ignore[arg-type]

    def test_short_sequence_returns_black(self) -> None:
        modifier = PDFModifier("dummy.pdf", "out.pdf")
        assert modifier._convert_color([0.5, 0.5]) == (0.0, 0.0, 0.0)


class TestModifierInit:
    """Tests for PDFModifier initialization."""

    def test_same_input_output_raises(self) -> None:
        with pytest.raises(ValueError, match="Input and output paths cannot be the same"):
            PDFModifier("same.pdf", "same.pdf")

    def test_nonexistent_file_raises_on_process(self, tmp_path: Path) -> None:
        modifier = PDFModifier(tmp_path / "missing.pdf", tmp_path / "out.pdf")
        spec = ReplacementSpec(replacements={"a": "b"})
        with pytest.raises(PDFReadError):
            modifier.process(spec)


class TestModifierContextManager:
    """Tests for context manager protocol."""

    def test_context_manager_opens_and_closes(self, tmp_path: Path) -> None:
        pdf_path = create_pdf(tmp_path / "test.pdf")
        output = tmp_path / "out.pdf"
        with PDFModifier(pdf_path, output) as modifier:
            assert modifier._doc is not None
            spec = ReplacementSpec(replacements={"Hello": "Goodbye"})
            result = modifier.process(spec)
            assert result.success

        assert modifier._doc is None

    def test_close_is_idempotent(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        modifier = PDFModifier(pdf_path, tmp_path / "out.pdf")
        modifier.close()
        modifier.close()  # Should not raise


class TestModifierEncryptedPDF:
    """Tests for password-protected PDF handling."""

    def test_encrypted_pdf_without_password_raises(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(tmp_path / "encrypted.pdf", text="Secret data")
        modifier = PDFModifier(pdf_path, tmp_path / "out.pdf")
        spec = ReplacementSpec(replacements={"Secret": "Public"})
        with pytest.raises(PDFPasswordError, match="password protected"):
            modifier.process(spec)

    def test_encrypted_pdf_wrong_password_raises(self, tmp_path: Path) -> None:
        pdf_path = create_encrypted_pdf(
            tmp_path / "encrypted.pdf",
            text="Secret data",
            user_pw="correct",
            owner_pw="owner",
        )
        modifier = PDFModifier(pdf_path, tmp_path / "out.pdf", password="wrong")
        spec = ReplacementSpec(replacements={"Secret": "Public"})
        with pytest.raises(PDFPasswordError, match="Incorrect password"):
            modifier.process(spec)

    def test_encrypted_pdf_correct_password(self, tmp_path: Path) -> None:
        full_perm = int(
            fitz.PDF_PERM_ACCESSIBILITY
            | fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
            | fitz.PDF_PERM_MODIFY
        )
        pdf_path = create_encrypted_pdf(
            tmp_path / "encrypted.pdf",
            text="Secret data",
            user_pw="correct",
            owner_pw="owner",
            permissions=full_perm,
        )
        modifier = PDFModifier(pdf_path, tmp_path / "out.pdf", password="correct")
        spec = ReplacementSpec(replacements={"Secret": "Public"})
        result = modifier.process(spec)
        assert result.success


class TestCrossSpanMatching:
    """Tests documenting the cross-span text matching limitation.

    PyMuPDF returns text in individual spans. Text that visually appears
    contiguous but is split across multiple spans cannot be matched as
    a single replacement target. This is a known limitation.
    """

    def test_single_span_matches(self, tmp_path: Path) -> None:
        """Text within a single span is matched correctly."""
        pdf_path = create_pdf(tmp_path / "single_span.pdf", text="Hello World")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello World": "Goodbye World"})
        result = modifier.process(spec)
        assert result.replacements_made == 1

    def test_cross_span_text_not_matched(self, tmp_path: Path) -> None:
        """Text split across spans is NOT matched — known limitation."""
        pdf_path = tmp_path / "multi_span.pdf"
        doc = fitz.open()
        page = doc.new_page()
        # Insert two spans with different fonts to prevent PyMuPDF merging
        page.insert_text((100, 100), "Hello ", fontsize=12, fontname="helv")
        page.insert_text((140, 100), "World", fontsize=12, fontname="cour")
        doc.save(str(pdf_path))
        doc.close()

        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"Hello World": "Goodbye World"})
        result = modifier.process(spec)
        # This documents the limitation: cross-span text won't match
        assert result.replacements_made == 0


class TestNoMatchReplacements:
    """Tests for replacement with no matching text."""

    def test_no_match_produces_zero_replacements(self, tmp_path: Path) -> None:
        pdf_path = create_pdf(tmp_path / "test.pdf")
        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"NONEXISTENT": "replacement"})
        result = modifier.process(spec)
        assert result.success
        assert result.replacements_made == 0
        assert result.pages_modified == 0

    def test_empty_page_pdf(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        output = tmp_path / "out.pdf"
        modifier = PDFModifier(pdf_path, output)
        spec = ReplacementSpec(replacements={"anything": "something"})
        result = modifier.process(spec)
        assert result.success
        assert result.replacements_made == 0
