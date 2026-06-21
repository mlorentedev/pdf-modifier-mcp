---
id: "FONT-001-custom-fonts"
type: task
status: active
tags: [core, fonts, custom-fonts, verification]
---

# Verification: FONT-001 Custom Font Support

## Evidence of Completion

### Unit Tests

```bash
# Run FontResolver tests
pytest tests/unit/test_font_resolver.py -v --cov=src/pdf_modifier_mcp/core/font_resolver --cov-report=term-missing

# Run custom font tests
pytest tests/unit/test_modifier_custom_fonts.py -v --cov=src/pdf_modifier_mcp/core/modifier --cov-report=term-missing

# Run embedded font tests
pytest tests/unit/test_analyzer_embedded_fonts.py -v --cov=src/pdf_modifier_mcp/core/analyzer --cov-report=term-missing
```

### Mutation Testing

```bash
mutmut run --paths-to-mutate=src/pdf_modifier_mcp/core/font_resolver.py
mutmut run --paths-to-mutate=src/pdf_modifier_mcp/core/modifier.py
```

### Integration Test

```bash
# Create test PDF, apply custom font replacement, verify embedded font
pytest tests/integration/test_custom_fonts.py -v
```

### Full Test Suite

```bash
make test
make check
```

## Acceptance Criteria Verification

### Task 1.1: FontProperties model
- [ ] `FontProperties` has all required fields
- [ ] `EmbeddedFontInfo` has all required fields
- [ ] Model validates fontfile path exists
- [ ] Unit tests pass

### Task 1.2: FontResolver class
- [ ] `resolve()` returns correct FontProperties for Base 14 fonts
- [ ] Enhanced detection works with font flags
- [ ] Custom font matching resolves to correct fontfile
- [ ] Fallback to Base 14 works when custom font not found
- [ ] Unit tests: 100% coverage

### Task 2.1: PDFModifier custom_fonts parameter
- [ ] `custom_fonts` dict parameter accepted
- [ ] Validation: custom_fonts values must be existing .ttf/.otf
- [ ] Replacement uses FontResolver
- [ ] `insert_text` passes fontfile when custom font matches
- [ ] Backward compatible: existing code works without custom_fonts

### Task 2.2: PDFModifier custom font tests
- [ ] Custom TTF font replacement works
- [ ] Custom OTF font replacement works
- [ ] Invalid font file error handled
- [ ] Custom font vs Base 14 priority correct

### Task 2.3: CLI integration
- [ ] `--custom-fonts KEY=PATH` argument works
- [ ] Parses into dict correctly
- [ ] Validates font files before processing
- [ ] Error message clear

### Task 3.1: extract_embedded_fonts
- [ ] Returns list of EmbeddedFontInfo
- [ ] Only returns embedded fonts
- [ ] Buffer integrity verified
- [ ] Page numbers tracked

### Task 3.2: Embedded font tests
- [ ] Extraction from PDF with embedded font works
- [ ] Empty result for Base 14 only PDF
- [ ] Buffer round-trip verified

### Task 3.3: MCP tools
- [ ] Enhanced inspect_fonts tool works
- [ ] New extract_fonts tool works
- [ ] MCP tools documented

### Task 4.1-4.3: Documentation
- [ ] Models have docstrings
- [ ] README documents custom font usage
- [ ] Integration test passes

## Manual Verification

### Custom Font Replacement
```bash
# Create a test PDF
python -c "
import fitz
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), 'Hello World', fontname='helv', fontsize=12)
doc.save('/tmp/test_input.pdf')
"

# Replace with custom font
pdf-modifier --input /tmp/test_input.pdf --output /tmp/test_output.pdf \
  --replacements "Hello World=Hello Custom" \
  --custom-fonts helv=C:/Windows/Fonts/arial.ttf

# Verify embedded font
python -c "
import fitz
doc = fitz.open('/tmp/test_output.pdf')
fonts = doc[0].get_fonts(full=True)
for f in fonts:
    print(f'xref={f[0]}, name={f[1]}, embed={f[4]}')
"
```

### Embedded Font Extraction
```bash
pdf-modifier --input /tmp/test_input.pdf --extract-fonts
```

## Quality Gates

- [ ] `make check` passes (lint + type + test)
- [ ] Coverage >= 80% global, >= 90% new code
- [ ] Mutation score >= 70%
- [ ] No new dependencies
- [ ] Backward compatible (existing tests pass)
