---
id: "FONT-001-custom-fonts"
type: adr
status: active
tags: [core, fonts, custom-fonts, font-resolution]
---

# ADR-007: Custom Font Support & Font Resolver

- **Date**: 2026-06-20
- **Status**: Proposed
- **Issue**: [#3](https://github.com/mlorentedev/pdf-modifier-mcp/issues/3)

## Context

The current `_get_font_properties()` in `modifier.py` maps PDF font names to Base 14 font codes using simple string matching. This approach:

1. Cannot handle custom/non-Base-14 fonts
2. Does not detect font style (italic, bold variations) reliably
3. Cannot embed custom font files (TTF/OTF)
4. Does not extract embedded fonts from source PDFs

Users need to:
- Provide custom font files for replacements
- Have better font attribute detection (bold, italic, serif, monospace)
- Extract embedded fonts from source PDFs for inspection

## Decisions

### Decision 1: FontResolver Pattern

**Create a new `FontResolver` class** that encapsulates font resolution logic. The existing `_get_font_properties()` is preserved as-is (core is sacred) and used as a fallback.

```python
class FontResolver:
    def resolve(self, font_name, font_flags=None, custom_fonts=None) -> FontProperties:
        ...
```

**Rationale**: Separates font resolution from the replacement engine. Makes font logic testable independently. Allows custom font injection without modifying core replacement flow.

### Decision 2: Custom Fonts via Dict Parameter

```python
class PDFModifier:
    def __init__(
        self,
        input_path,
        output_path,
        password=None,
        max_file_size=...,
        custom_fonts: dict[str, str] | None = None,  # alias -> path
    ):
```

- `custom_fonts`: map of alias names to file paths
- Example: `{"myfont": "/path/to/custom.ttf", "bold": "/path/to/bold.otf"}`
- Aliases are matched against resolved font names
- Validation: file must exist and be valid TTF/OTF

**Rationale**: Simple API, explicit mapping. No global state. Compatible with existing `ReplacementSpec` pattern.

### Decision 3: PyMuPDF fontfile Integration

PyMuPDF's `page.insert_text()` accepts `fontfile` parameter directly:

```python
page.insert_text(point, text, fontname="arial", fontfile="/path/to/arial.ttf", fontsize=12)
```

We leverage this — no need for a font registration system. The `FontResolver` returns `FontProperties.fontfile` when a custom font matches.

**Rationale**: PyMuPDF handles font embedding internally. No custom embedding logic needed. Simpler and more reliable.

### Decision 4: Embedded Font Extraction via get_fonts + extract_font

```python
class PDFAnalyzer:
    def extract_embedded_fonts(self) -> list[EmbeddedFontInfo]:
        """Extract metadata and buffer of all embedded fonts."""
```

Uses:
- `page.get_fonts(full=True)` → lists fonts with xref, name, type, encoding, embed, file
- `doc.extract_font(xref)` → returns `(name, type, subtype, buffer)`

**Rationale**: PyMuPDF provides all necessary APIs. No custom parsing needed.

### Decision 5: Enhanced Font Detection

Improved detection uses:
- Font name heuristics (existing, preserved)
- Font flags from PyMuPDF span dict (if available)
- Better bold/italic/serif/monospace detection

**Rationale**: Backward compatible. Only enhances detection when flags are available.

## Consequences

### Positive
- Custom fonts work for any TTF/OTF
- Better font style detection
- Embedded font inspection capability
- Clean separation of concerns (FontResolver)
- Backward compatible (existing API unchanged)

### Negative
- ~440 LOC added
- Custom font files must be distributed with the application
- Font file paths are absolute — relative paths need resolution
- Font resolution is now two-layer (FontResolver → _get_font_properties fallback)

### Out of Scope
- Font subsetting
- Font hinting/rendering optimization
- CJK font auto-detection (covered in ML-001)
- Font conversion (TTF → Type1)

## References

- Issue: [#3](https://github.com/mlorentedev/pdf-modifier-mcp/issues/3)
- Pattern: `pattern-architecture` (monolith structure)
- Pattern: `pattern-testing-standards` (TDD)
- PyMuPDF docs: `fitz.Font.__init__`, `page.insert_text`, `doc.extract_font`
