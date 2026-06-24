"""Font resolution with enhanced detection and custom font support."""

from __future__ import annotations

from pathlib import Path

from .models import FontProperties


class FontResolver:
    """Resolves font properties from PDF spans with enhanced detection.

    Combines Base 14 font name mapping with font flag analysis and custom
    font file resolution. Preserves existing ``_get_font_properties`` behavior
    as the fallback path.

    Example:
        >>> resolver = FontResolver()
        >>> props = resolver.resolve("Arial-BoldMT")
        >>> props.fontname
        'HeBo'
        >>> props = resolver.resolve("myfont", custom_fonts={"myfont": "/path/to/font.ttf"})
        >>> props.fontfile
        '/path/to/font.ttf'
    """

    # Base 14 font name patterns: (substring, fontname, bold, italic, serif, mono)
    # Order matters: more specific patterns first.
    _BASE14_PATTERNS: list[tuple[str, str, bool, bool, bool, bool]] = [
        # Courier (monospaced)
        ("courier-boldoblique", "CoBo", True, True, False, True),
        ("courier-oblique", "Couri", False, True, False, True),
        ("courier-bold", "CoBo", True, False, False, True),
        ("courier", "Cour", False, False, False, True),
        # Times (serif)
        ("times-bolditalic", "TiBo", True, True, True, False),
        ("times-italic", "TiI", False, True, True, False),
        ("times-bold", "TiBo", True, False, True, False),
        ("times", "TiRo", False, False, True, False),
        ("serif", "TiRo", False, False, True, False),
        # Helvetica (and Arial — Arial is a Helvetica substitute in PDFs)
        ("helvetica-boldoblique", "HeBo", True, True, False, False),
        ("helvetica-oblique", "helvi", False, True, False, False),
        ("helvetica-bold", "HeBo", True, False, False, False),
        ("helvetica-italic", "helvi", False, True, False, False),
        ("helvetica", "helv", False, False, False, False),
        ("arial-boldoblique", "HeBo", True, True, False, False),
        ("arial-oblique", "helvi", False, True, False, False),
        ("arial-bold", "HeBo", True, False, False, False),
        ("arial-italic", "helvi", False, True, False, False),
        ("arial", "helv", False, False, False, False),
        # ZapfDingbats
        ("zapfdingbats", "ZaDb", False, False, False, False),
    ]

    def resolve(
        self,
        font_name: str,
        font_flags: dict[str, int] | None = None,
        custom_fonts: dict[str, str] | None = None,
    ) -> FontProperties:
        """Resolve font properties from name, flags, and custom fonts.

        Resolution order:
        1. Custom font match (if alias matches font name directly)
        2. Base 14 font name pattern matching
        3. Custom font match by resolved Base 14 code (if alias matches)
        4. Fallback to Helvetica

        Args:
            font_name: Font name from PDF span (e.g. "Arial-BoldMT").
            font_flags: Optional PyMuPDF font flags dict with keys
                        ``bold``, ``italic``, ``mono``, ``serif`` (0 or 1).
            custom_fonts: Optional map of alias -> file path for custom fonts.
                          Aliases can match either the raw font name or a
                          resolved Base 14 code (e.g. "helv").

        Returns:
            FontProperties with resolved fontname, fontfile, and style flags.
        """
        # Step 1: Check custom fonts by raw font name
        if custom_fonts and font_name in custom_fonts:
            font_path = custom_fonts[font_name]
            if self._is_valid_font_file(font_path):
                return FontProperties(
                    fontname=font_name,  # Use font_name as-is (may be Base 14 name)
                    fontfile=font_path,
                    is_bold=font_flags.get("bold", 0) == 1 if font_flags else False,
                    is_italic=font_flags.get("italic", 0) == 1 if font_flags else False,
                    is_serif=font_flags.get("serif", 0) == 1 if font_flags else False,
                    is_monospaced=font_flags.get("mono", 0) == 1 if font_flags else False,
                    embed=True,
                )

        # Step 2: Base 14 font name matching
        resolved_fontname: str | None = None
        is_bold, is_italic, is_serif, is_monospaced = False, False, False, False

        for pattern, fontname, fb, fi, fs, fm in self._BASE14_PATTERNS:
            if pattern in font_name.lower():
                resolved_fontname = fontname
                is_bold, is_italic, is_serif, is_monospaced = fb, fi, fs, fm
                break

        if resolved_fontname is not None:
            # Step 3: Apply font flag overrides
            if font_flags:
                is_bold = is_bold or font_flags.get("bold", 0) == 1
                is_italic = is_italic or font_flags.get("italic", 0) == 1
                is_serif = is_serif or font_flags.get("serif", 0) == 1
                is_monospaced = is_monospaced or font_flags.get("mono", 0) == 1

            # Step 4: Check if custom font overrides this Base 14 code
            if custom_fonts and resolved_fontname in custom_fonts:
                font_path = custom_fonts[resolved_fontname]
                if self._is_valid_font_file(font_path):
                    return FontProperties(
                        fontname=resolved_fontname,
                        fontfile=font_path,
                        is_bold=is_bold,
                        is_italic=is_italic,
                        is_serif=is_serif,
                        is_monospaced=is_monospaced,
                        embed=True,
                    )

            return FontProperties(
                fontname=resolved_fontname,
                is_bold=is_bold,
                is_italic=is_italic,
                is_serif=is_serif,
                is_monospaced=is_monospaced,
                embed=True,
            )

        # Step 5: Fallback to Helvetica
        return FontProperties(
            fontname="helv",
            is_bold=font_flags.get("bold", 0) == 1 if font_flags else False,
            is_italic=font_flags.get("italic", 0) == 1 if font_flags else False,
            is_serif=font_flags.get("serif", 0) == 1 if font_flags else False,
            is_monospaced=font_flags.get("mono", 0) == 1 if font_flags else False,
            embed=True,
        )

    @staticmethod
    def _is_valid_font_file(path: str) -> bool:
        """Check if a path points to a valid TTF or OTF font file."""
        p = Path(path)
        if not p.is_file():
            return False
        return p.suffix.lower() in (".ttf", ".otf")
