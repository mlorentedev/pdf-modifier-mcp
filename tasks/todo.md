# pdf-modifier-mcp — Backlog

> MCP server + CLI for PDF text replacement with style preservation.

## P0 — High Priority

- [ ] **File size validation**: No max file size check before processing. Large PDFs could cause OOM.
- [x] ~~**Cross-span text matching**~~: Documented as known limitation in troubleshooting guide + test proving behavior.

## P1 — Medium Priority

- [ ] **Programmatic API examples in README**: Only CLI/MCP usage shown. Add Python library usage examples (`from pdf_modifier_mcp import PDFModifier`).
- [ ] **Batch operations**: Support processing multiple PDFs in a single invocation (directory mode or glob pattern).
- [ ] **Test large PDFs**: No performance/memory tests for documents with many pages.

## P2 — Low Priority / Nice-to-Have

- [ ] **Font width caching**: Font widths recalculated per text insertion. Cache for repeated same-font replacements.
- [ ] **Silent color fallback**: Invalid color inputs default to black `(0,0,0)` without warning. Log a warning.
- [ ] **Page range support**: Allow restricting replacements to specific page ranges.

## Done

- [x] **Remove unused exception classes**: Removed `FileSizeError` and `TextNotFoundError` (dead code).
- [x] **Drop pytest-asyncio**: Removed unused dependency. All tools are synchronous by design.
- [x] **Test encrypted PDFs**: Added tests for password-protected PDFs (modifier + analyzer + MCP).
- [x] **mypy strict mode**: Enabled `strict = true`, fixed all type errors.
- [x] **Ruff TCH + A rules**: Added type-checking import guards and builtin shadowing rules.
- [x] **Python 3.12+ target**: Bumped requires-python, CI matrix, and classifiers.
- [x] **Coverage threshold**: 94% coverage with `--cov-fail-under=80` enforced.
- [x] **Codecov CI integration**: Added upload step to CI workflow.
- [x] **SECURITY.md**: Added responsible disclosure policy.
- [x] **CODE_OF_CONDUCT.md**: Added Contributor Covenant v2.1.
- [x] **Docs site expansion**: Added MCP Tools reference, Troubleshooting guide, Architecture page.
- [x] **Fix PDFPasswordError propagation**: Analyzer methods now correctly propagate password errors instead of wrapping them as PDFReadError.
- [x] **`from __future__ import annotations`**: Added to all source and test files.
