"""Tests for FontProperties and EmbeddedFontInfo models."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdf_modifier.core.models import EmbeddedFontInfo, FontProperties


class TestFontProperties:
    """Tests for FontProperties model."""

    def test_basic_font_properties(self) -> None:
        props = FontProperties(
            fontname="helv",
            is_bold=False,
            is_italic=False,
            is_serif=False,
            is_monospaced=False,
            embed=True,
        )
        assert props.fontname == "helv"
        assert props.fontfile is None
        assert props.is_bold is False
        assert props.is_italic is False
        assert props.is_serif is False
        assert props.is_monospaced is False
        assert props.embed is True

    def test_custom_font_with_file(self, tmp_path: Path) -> None:
        """FontProperties accepts a valid fontfile path."""
        font_file = tmp_path / "arial.ttf"
        font_file.write_bytes(b"fake ttf content")

        props = FontProperties(
            fontname="arial",
            fontfile=str(font_file),
            is_bold=False,
            is_italic=False,
            is_serif=False,
            is_monospaced=False,
            embed=True,
        )
        assert props.fontname == "arial"
        assert props.fontfile == str(font_file)
        assert Path(props.fontfile).exists()

    def test_custom_font_invalid_path_raises(self, tmp_path: Path) -> None:
        """FontProperties rejects a non-existent fontfile path."""
        non_existent = str(tmp_path / "nonexistent.ttf")

        with pytest.raises(ValueError, match="font file does not exist"):
            FontProperties(
                fontname="arial",
                fontfile=non_existent,
                is_bold=False,
                is_italic=False,
                is_serif=False,
                is_monospaced=False,
                embed=True,
            )

    def test_bold_font_properties(self) -> None:
        props = FontProperties(
            fontname="arial-bold",
            fontfile=None,
            is_bold=True,
            is_italic=False,
            is_serif=False,
            is_monospaced=False,
            embed=True,
        )
        assert props.is_bold is True

    def test_italic_font_properties(self) -> None:
        props = FontProperties(
            fontname="arial-italic",
            fontfile=None,
            is_bold=False,
            is_italic=True,
            is_serif=False,
            is_monospaced=False,
            embed=True,
        )
        assert props.is_italic is True

    def test_serif_font_properties(self) -> None:
        props = FontProperties(
            fontname="times-roman",
            fontfile=None,
            is_bold=False,
            is_italic=False,
            is_serif=True,
            is_monospaced=False,
            embed=True,
        )
        assert props.is_serif is True

    def test_monospaced_font_properties(self) -> None:
        props = FontProperties(
            fontname="courier",
            fontfile=None,
            is_bold=False,
            is_italic=False,
            is_serif=False,
            is_monospaced=True,
            embed=True,
        )
        assert props.is_monospaced is True

    def test_embed_false(self) -> None:
        props = FontProperties(
            fontname="helv",
            embed=False,
        )
        assert props.embed is False

    def test_all_flags_true(self) -> None:
        """Bold italic serif font (e.g. Times-BoldItalic)."""
        props = FontProperties(
            fontname="times-bold-italic",
            is_bold=True,
            is_italic=True,
            is_serif=True,
            is_monospaced=False,
            embed=True,
        )
        assert props.is_bold is True
        assert props.is_italic is True
        assert props.is_serif is True


class TestEmbeddedFontInfo:
    """Tests for EmbeddedFontInfo model."""

    def test_basic_embedded_font(self) -> None:
        info = EmbeddedFontInfo(
            name="Arial Regular",
            type="TrueType",
            subtype="ttf",
            buffer=b"fake font buffer",
            page_numbers=[1, 2],
        )
        assert info.name == "Arial Regular"
        assert info.type == "TrueType"
        assert info.subtype == "ttf"
        assert info.buffer == b"fake font buffer"
        assert info.page_numbers == [1, 2]

    def test_empty_page_numbers(self) -> None:
        """Embedded font with no page numbers is valid."""
        info = EmbeddedFontInfo(
            name="Helvetica",
            type="Type1",
            subtype="helv",
            buffer=b"",
            page_numbers=[],
        )
        assert info.page_numbers == []

    def test_empty_buffer_valid(self) -> None:
        """Empty buffer is valid (e.g. system fonts with no embedded data)."""
        info = EmbeddedFontInfo(
            name="Helvetica",
            type="Type1",
            subtype="helv",
            buffer=b"",
            page_numbers=[1],
        )
        assert info.buffer == b""

    def test_font_type_variants(self) -> None:
        """Test various font type values."""
        for font_type in ("TrueType", "Type1", "Type0", "CID", "Unknown"):
            info = EmbeddedFontInfo(
                name="Test",
                type=font_type,
                subtype="test",
                buffer=b"data",
                page_numbers=[1],
            )
            assert info.type == font_type

    def test_multiple_pages(self) -> None:
        """Font embedded across multiple pages."""
        info = EmbeddedFontInfo(
            name="CustomFont",
            type="TrueType",
            subtype="ttf",
            buffer=b"font data here",
            page_numbers=[1, 3, 5, 7],
        )
        assert len(info.page_numbers) == 4
