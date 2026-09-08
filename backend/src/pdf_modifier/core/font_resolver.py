"""Font resolution with enhanced detection and custom font support."""

from __future__ import annotations

from pathlib import Path

from .models import FontProperties


class FontResolver:
    """Resolves font properties from PDF spans with enhanced detection.

    Combines Base 14 font name mapping with font flag analysis and custom
    font file resolution.

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
        # Common embedded families (DejaVu, Noto, Nimbus) — keep the specific
        # font (mono/serif) BEFORE the generic sans family so a monospaced
        # DejaVuSansMono is not misread as a plain sans font.
        ("dejavusansmono", "Cour", False, False, False, True),
        ("dejavusans", "helv", False, False, False, False),
        ("dejavuserif", "TiRo", False, False, True, False),
        ("notosansmono", "Cour", False, False, False, True),
        ("notosans", "helv", False, False, False, False),
        ("notoserif", "TiRo", False, False, True, False),
        ("nimbussans", "helv", False, False, False, False),
        ("nimbusroman", "TiRo", False, False, True, False),
        # Liberation fonts (metric-compatible with Arial/Helvetica and Times).
        # They are embedded in many PDFs as ``XXXXXX+LiberationSans``. Keep the
        # specific weight/style variants BEFORE the generic family name so that
        # bold/italic are preserved in a faithful replica instead of falling
        # back to the plain (non-bold) Helvetica code.
        ("liberationsans-bolditalic", "HeBo", True, True, False, False),
        ("liberationsans-bold", "HeBo", True, False, False, False),
        ("liberationsans-italic", "helvi", False, True, False, False),
        ("liberationsans", "helv", False, False, False, False),
        ("liberationserif-bolditalic", "TiBo", True, True, True, False),
        ("liberationserif-bold", "TiBo", True, False, True, False),
        ("liberationserif-italic", "TiI", False, True, True, False),
        ("liberationserif", "TiRo", False, False, True, False),
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
            # Grade weight/style from the font name when it encodes it
            # (e.g. "DejaVuSans-Bold") so name-only detection stays correct even
            # when the span flags are absent.
            name_lower = font_name.lower()
            if "bold" in name_lower:
                is_bold = True
            if "italic" in name_lower or "oblique" in name_lower:
                is_italic = True

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

            # Upgrade the family code to the bold/italic variant. Previously the
            # code stayed regular (e.g. "helv") even when the name/flags said
            # bold, silently dropping the weight.
            resolved_fontname = self._apply_style_to_fontname(resolved_fontname, is_bold, is_italic)
            return FontProperties(
                fontname=resolved_fontname,
                is_bold=is_bold,
                is_italic=is_italic,
                is_serif=is_serif,
                is_monospaced=is_monospaced,
                embed=True,
            )

        # Step 5: Fallback to Helvetica (family unknown -> assume sans)
        name_lower = font_name.lower()
        is_bold = ("bold" in name_lower) or (
            font_flags.get("bold", 0) == 1 if font_flags else False
        )
        is_italic = ("italic" in name_lower or "oblique" in name_lower) or (
            font_flags.get("italic", 0) == 1 if font_flags else False
        )
        is_serif = font_flags.get("serif", 0) == 1 if font_flags else False
        is_monospaced = font_flags.get("mono", 0) == 1 if font_flags else False
        return FontProperties(
            fontname=self._apply_style_to_fontname("helv", is_bold, is_italic),
            is_bold=is_bold,
            is_italic=is_italic,
            is_serif=is_serif,
            is_monospaced=is_monospaced,
            embed=True,
        )

    @staticmethod
    def _apply_style_to_fontname(
        base_code: str,
        is_bold: bool,
        is_italic: bool,
    ) -> str:
        """Upgrade a Base 14 family code to its bold/italic variant.

        PyMuPDF uses a distinct font code per weight/style of the same family.
        The resolver previously kept the plain family code (e.g. ``helv``) even
        when the font name or span flags indicated bold/italic, silently
        dropping the weight. This maps (family, bold, italic) to the matching
        Base 14 code.
        """
        sans = ("helv", "HeBo", "helvi")
        serif = ("TiRo", "TiBo", "TiI")
        mono = ("Cour", "CoBo", "Couri")
        if base_code in sans:
            if is_bold:
                return "HeBo"
            if is_italic:
                return "helvi"
            return "helv"
        if base_code in serif:
            if is_bold:
                return "TiBo"
            if is_italic:
                return "TiI"
            return "TiRo"
        if base_code in mono:
            if is_bold:
                return "CoBo"
            if is_italic:
                return "Couri"
            return "Cour"
        return base_code

    @staticmethod
    def _is_valid_font_file(path: str) -> bool:
        """Check if a path points to a valid TTF or OTF font file."""
        p = Path(path)
        if not p.is_file():
            return False
        return p.suffix.lower() in (".ttf", ".otf")
