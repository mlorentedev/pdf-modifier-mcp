---
id: "FONT-001-custom-fonts"
type: task
status: active
tags: [core, fonts, custom-fonts]
---

# Tasks: FONT-001 Custom Font Support & Font Resolver

## Phase 1: Foundation (FontResolver + Models)

### Task 1.1: FontProperties model
- **File**: `src/pdf_modifier_mcp/core/models.py`
- **Description**: Add `FontProperties` and `EmbeddedFontInfo` Pydantic models
- **Acceptance**:
  - `FontProperties` has: fontname, fontfile (optional), is_bold, is_italic, is_serif, is_monospaced, embed
  - `EmbeddedFontInfo` has: name, type, subtype, buffer (bytes), page_numbers
  - Model validates fontfile path exists when provided
- **LOC**: ~30

### Task 1.2: FontResolver class
- **File**: `src/pdf_modifier_mcp/core/font_resolver.py` (NEW)
- **Description**: Core font resolution logic with enhanced detection
- **Acceptance**:
  - `resolve(font_name, font_flags=None, custom_fonts=None) -> FontProperties`
  - Enhanced detection: bold, italic, serif, monospace from font flags
  - Custom font matching: resolves alias to fontfile
  - Falls back to `_get_font_properties` logic for Base 14 fonts
  - Unit tests: 100% coverage
- **LOC**: ~120

### Task 1.3: FontResolver tests
- **File**: `tests/unit/test_font_resolver.py` (NEW)
- **Description**: Comprehensive tests for FontResolver
- **Acceptance**:
  - Test Base 14 font resolution (existing behavior preserved)
  - Test enhanced detection with font flags
  - Test custom font matching
  - Test invalid font file handling
  - Test fallback to Base 14 when custom font not found
- **LOC**: ~80

## Phase 2: Custom Font Integration

### Task 2.1: PDFModifier custom_fonts parameter
- **File**: `src/pdf_modifier_mcp/core/modifier.py`
- **Description**: Add `custom_fonts` parameter and integrate FontResolver
- **Acceptance**:
  - `PDFModifier.__init__` accepts `custom_fonts: dict[str, str] | None = None`
  - Validation: custom_fonts values must be existing .ttf/.otf files
  - `_match_single_span` and `_build_cross_span_item` use FontResolver
  - `insert_text` passes `fontfile` when custom font matches
  - Backward compatible: existing code works without custom_fonts
- **LOC**: ~60

### Task 2.2: PDFModifier custom font tests
- **File**: `tests/unit/test_modifier_custom_fonts.py` (NEW)
- **Description**: Tests for custom font integration
- **Acceptance**:
  - Test replacement with custom TTF font
  - Test replacement with custom OTF font
  - Test invalid font file error handling
  - Test custom font vs Base 14 priority
  - Test font file not found error
- **LOC**: ~60

### Task 2.3: CLI integration for custom fonts
- **File**: `src/pdf_modifier_mcp/interfaces/cli.py`
- **Description**: Add `--custom-fonts` CLI argument
- **Acceptance**:
  - `--custom-fonts KEY=PATH` (repeatable) argument
  - Parses into dict and passes to PDFModifier
  - Validates font files exist before processing
  - Error message: "Custom font file not found: /path/to/font.ttf"
- **LOC**: ~20

## Phase 3: Embedded Font Extraction

### Task 3.1: PDFAnalyzer.extract_embedded_fonts
- **File**: `src/pdf_modifier_mcp/core/analyzer.py`
- **Description**: Add method to extract embedded font metadata and buffers
- **Acceptance**:
  - `extract_embedded_fonts() -> list[EmbeddedFontInfo]`
  - Uses `page.get_fonts(full=True)` + `doc.extract_font(xref)`
  - Returns font name, type, subtype, buffer, page numbers
  - Only returns fonts that are actually embedded (not Type1 system fonts)
  - Unit tests with mocked PDF
- **LOC**: ~40

### Task 3.2: Embedded font extraction tests
- **File**: `tests/unit/test_analyzer_embedded_fonts.py` (NEW)
- **Description**: Tests for embedded font extraction
- **Acceptance**:
  - Test extraction from PDF with embedded custom font
  - Test extraction from PDF with only Base 14 fonts (empty result)
  - Test buffer integrity (round-trip: extract → save → reload)
  - Test page number tracking
- **LOC**: ~40

### Task 3.3: MCP tool for font inspection
- **File**: `src/pdf_modifier_mcp/interfaces/mcp.py`
- **Description**: Add `inspect_fonts` tool enhancement with embedded font info
- **Acceptance**:
  - Existing `inspect_fonts` tool enhanced with embedded font metadata
  - New `extract_fonts` tool: extracts embedded font buffers
  - MCP tools documented with descriptions
- **LOC**: ~30

## Phase 4: Documentation & Polish

### Task 4.1: Update models.py docstrings
- **File**: `src/pdf_modifier_mcp/core/models.py`
- **Description**: Add docstrings and examples for new models
- **Acceptance**: All new models have docstrings with usage examples

### Task 4.2: README update
- **File**: `README.md`
- **Description**: Document custom font usage
- **Acceptance**:
  - CLI example: `pdf-modifier --custom-fonts myfont=/path/to/font.ttf ...`
  - Python API example with custom_fonts dict
  - Embedded font extraction example

### Task 4.3: Integration test
- **File**: `tests/integration/test_custom_fonts.py` (NEW)
- **Description**: End-to-end test with real PDF + custom font
- **Acceptance**:
  - Create PDF with text
  - Replace text using custom TTF font
  - Verify output PDF has embedded custom font
  - Verify text rendering is correct
- **LOC**: ~30

## Summary

| Phase | Tasks | Est. LOC | Est. Days |
|-------|-------|----------|-----------|
| 1. Foundation | 3 | ~230 | 1.5 |
| 2. Custom Font Integration | 3 | ~140 | 1 |
| 3. Embedded Font Extraction | 3 | ~110 | 0.75 |
| 4. Documentation & Polish | 3 | ~80 | 0.5 |
| **Total** | **12** | **~560** | **~3.75** |

## TDD Order

1. Task 1.1 → models (blue)
2. Task 1.2 → FontResolver (green)
3. Task 1.3 → FontResolver tests (green)
4. Task 2.1 → PDFModifier integration (green)
5. Task 2.2 → custom font tests (green)
6. Task 2.3 → CLI integration (green)
7. Task 3.1 → extract_embedded_fonts (green)
8. Task 3.2 → embedded font tests (green)
9. Task 3.3 → MCP tools (green)
10. Task 4.1-4.3 → docs + integration (green)
