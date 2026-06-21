"""Tests for FontResolver class."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from pdf_modifier_mcp.core.font_resolver import FontResolver


class TestFontResolverResolve:
    """Tests for FontResolver.resolve()."""

    @pytest.fixture
    def resolver(self) -> FontResolver:
        return FontResolver()

    def test_base14_helv(self, resolver: FontResolver) -> None:
        props = resolver.resolve("ArialMT")
        assert props.fontname == "helv"
        assert props.fontfile is None
        assert props.is_bold is False
        assert props.is_italic is False

    def test_base14_helv_bold(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Arial-BoldMT")
        assert props.fontname == "HeBo"
        assert props.is_bold is True

    def test_base14_helv_italic(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Arial-ItalicMT")
        assert props.fontname == "helvi"
        assert props.is_italic is True

    def test_base14_helv_bold_italic(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Helvetica-BoldOblique")
        assert props.fontname == "HeBo"  # PyMuPDF doesn't have helvbi as simple code
        assert props.is_bold is True

    def test_base14_times_roman(self, resolver: FontResolver) -> None:
        props = resolver.resolve("TimesNewRoman")
        assert props.fontname in ("TiRo", "TiBo")  # depends on detection
        assert props.is_serif is True

    def test_base14_times_bold(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Times-Bold")
        assert props.fontname == "TiBo"
        assert props.is_bold is True

    def test_base14_courier(self, resolver: FontResolver) -> None:
        props = resolver.resolve("CourierNew")
        assert props.fontname == "Cour"
        assert props.is_monospaced is True

    def test_base14_courier_bold(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Courier-Bold")
        assert props.fontname == "CoBo"
        assert props.is_bold is True
        assert props.is_monospaced is True

    def test_base14_zapfdingbats(self, resolver: FontResolver) -> None:
        props = resolver.resolve("ZapfDingbats")
        assert props.fontname == "ZaDb"

    def test_default_fallback(self, resolver: FontResolver) -> None:
        """Unknown font names fall back to Helvetica."""
        props = resolver.resolve("SomeWeirdFont123")
        assert props.fontname == "helv"

    def test_empty_font_name(self, resolver: FontResolver) -> None:
        """Empty font name falls back to Helvetica."""
        props = resolver.resolve("")
        assert props.fontname == "helv"

    def test_serif_detection(self, resolver: FontResolver) -> None:
        """Font names containing 'serif' or 'times' are detected as serif."""
        props = resolver.resolve("MySerifFont")
        assert props.is_serif is True

    def test_monospace_detection(self, resolver: FontResolver) -> None:
        """Font names containing 'courier' are detected as monospaced."""
        props = resolver.resolve("Courier")
        assert props.is_monospaced is True


class TestFontResolverWithFontFlags:
    """Tests for FontResolver.resolve() with font_flags parameter."""

    @pytest.fixture
    def resolver(self) -> FontResolver:
        return FontResolver()

    def test_flags_override_bold(self, resolver: FontResolver) -> None:
        """Font flags can override name-based detection."""
        props = resolver.resolve(
            "SomeFont",
            font_flags={"bold": 1, "italic": 0, "mono": 0, "serif": 0},
        )
        assert props.is_bold is True
        assert props.is_italic is False

    def test_flags_override_italic(self, resolver: FontResolver) -> None:
        props = resolver.resolve(
            "SomeFont",
            font_flags={"bold": 0, "italic": 1, "mono": 0, "serif": 0},
        )
        assert props.is_italic is True

    def test_flags_override_serif(self, resolver: FontResolver) -> None:
        props = resolver.resolve(
            "SomeFont",
            font_flags={"bold": 0, "italic": 0, "mono": 0, "serif": 1},
        )
        assert props.is_serif is True

    def test_flags_override_monospace(self, resolver: FontResolver) -> None:
        props = resolver.resolve(
            "SomeFont",
            font_flags={"bold": 0, "italic": 0, "mono": 1, "serif": 0},
        )
        assert props.is_monospaced is True

    def test_flags_combined(self, resolver: FontResolver) -> None:
        """Multiple flags can be set simultaneously."""
        props = resolver.resolve(
            "SomeFont",
            font_flags={"bold": 1, "italic": 1, "mono": 0, "serif": 1},
        )
        assert props.is_bold is True
        assert props.is_italic is True
        assert props.is_serif is True
        assert props.is_monospaced is False

    def test_flags_none(self, resolver: FontResolver) -> None:
        """None flags behave the same as no flags."""
        props1 = resolver.resolve("ArialMT")
        props2 = resolver.resolve("ArialMT", font_flags=None)
        assert props1.fontname == props2.fontname
        assert props1.is_bold == props2.is_bold

    def test_flags_empty_dict(self, resolver: FontResolver) -> None:
        """Empty dict behaves the same as no flags."""
        props1 = resolver.resolve("ArialMT")
        props2 = resolver.resolve("ArialMT", font_flags={})
        assert props1.fontname == props2.fontname


class TestFontResolverWithCustomFonts:
    """Tests for FontResolver.resolve() with custom_fonts parameter."""

    @pytest.fixture
    def resolver(self) -> FontResolver:
        return FontResolver()

    def test_custom_font_match(self, resolver: FontResolver, tmp_path: Path) -> None:
        """Custom font is matched when alias matches font name."""
        font_file = tmp_path / "myfont.ttf"
        font_file.write_bytes(b"fake ttf")

        custom_fonts = {"myfont": str(font_file)}
        props = resolver.resolve("myfont", custom_fonts=custom_fonts)

        assert props.fontname == "myfont"
        assert props.fontfile == str(font_file)

    def test_custom_font_no_match(self, resolver: FontResolver, tmp_path: Path) -> None:
        """Custom font is not used when alias doesn't match."""
        font_file = tmp_path / "myfont.ttf"
        font_file.write_bytes(b"fake ttf")

        custom_fonts = {"myfont": str(font_file)}
        props = resolver.resolve("ArialMT", custom_fonts=custom_fonts)

        # Falls back to Base 14 detection
        assert props.fontfile is None

    def test_custom_font_priority_over_base14(self, resolver: FontResolver, tmp_path: Path) -> None:
        """Custom font takes priority over Base 14 mapping."""
        font_file = tmp_path / "helv.ttf"
        font_file.write_bytes(b"fake ttf")

        custom_fonts = {"helv": str(font_file)}
        props = resolver.resolve("helv", custom_fonts=custom_fonts)

        assert props.fontname == "helv"
        assert props.fontfile == str(font_file)

    def test_custom_font_missing_file(self, resolver: FontResolver, tmp_path: Path) -> None:
        """Custom font with missing file falls back to Base 14."""
        custom_fonts = {"nonexistent": str(tmp_path / "missing.ttf")}
        props = resolver.resolve("nonexistent", custom_fonts=custom_fonts)

        # Falls back because file doesn't exist
        assert props.fontfile is None

    def test_custom_font_wrong_extension(self, resolver: FontResolver, tmp_path: Path) -> None:
        """Custom font with non-TTF/OTF extension is ignored."""
        font_file = tmp_path / "myfont.txt"
        font_file.write_bytes(b"not a font")

        custom_fonts = {"myfont": str(font_file)}
        props = resolver.resolve("myfont", custom_fonts=custom_fonts)

        assert props.fontfile is None

    def test_custom_font_otf(self, resolver: FontResolver, tmp_path: Path) -> None:
        """Custom OTF font is accepted."""
        font_file = tmp_path / "myfont.otf"
        font_file.write_bytes(b"fake otf")

        custom_fonts = {"myfont": str(font_file)}
        props = resolver.resolve("myfont", custom_fonts=custom_fonts)

        assert props.fontfile == str(font_file)


class TestFontResolverFallback:
    """Tests that FontResolver preserves existing _get_font_properties behavior."""

    @pytest.fixture
    def resolver(self) -> FontResolver:
        return FontResolver()

    def test_helvetica_default(self, resolver: FontResolver) -> None:
        props = resolver.resolve("ArialMT")
        assert props.fontname == "helv"

    def test_helvetica_bold(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Arial-BoldMT")
        assert props.fontname == "HeBo"

    def test_courier(self, resolver: FontResolver) -> None:
        props = resolver.resolve("CourierNew")
        assert props.fontname == "Cour"

    def test_courier_bold(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Courier-Bold")
        assert props.fontname == "CoBo"

    def test_times_roman(self, resolver: FontResolver) -> None:
        props = resolver.resolve("TimesNewRoman")
        # Should resolve to a Times font (TiRo or TiBo depending on detection)
        assert props.fontname.startswith("Ti")

    def test_times_bold(self, resolver: FontResolver) -> None:
        props = resolver.resolve("Times-Bold")
        assert props.fontname == "TiBo"

    def test_zapfdingbats(self, resolver: FontResolver) -> None:
        props = resolver.resolve("ZapfDingbats")
        assert props.fontname == "ZaDb"
