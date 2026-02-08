# pdf-modifier-mcp — Backlog

> MCP server + CLI for PDF text replacement with style preservation.

## P0 — High Priority

- [ ] **Remove unused exception classes**: `FileSizeError` and `TextNotFoundError` defined in `exceptions.py` but never raised. Either wire them up or remove dead code.
- [ ] **File size validation**: No max file size check before processing. Large PDFs could cause OOM. Add `FileSizeError` enforcement.
- [ ] **Cross-span text matching**: Replacement only works within individual text spans. If target text is split across spans by PyMuPDF, it won't match. Document limitation or implement span-merging logic.

## P1 — Medium Priority

- [ ] **Programmatic API examples in README**: Only CLI/MCP usage shown. Add Python library usage examples (`from pdf_modifier_mcp import PDFModifier`).
- [ ] **Test encrypted PDFs**: No test coverage for password-protected PDFs. Add test for `PDFReadError` handling.
- [ ] **Test large PDFs**: No performance/memory tests for documents with many pages.
- [ ] **Batch operations**: Support processing multiple PDFs in a single invocation (directory mode or glob pattern).
- [ ] **Async MCP tools**: `pytest-asyncio` is a dependency but all MCP tools are synchronous. Either implement async or drop the dependency.

## P2 — Low Priority / Nice-to-Have

- [ ] **Font width caching**: Font widths recalculated per text insertion. Cache for repeated same-font replacements.
- [ ] **Silent color fallback**: Invalid color inputs default to black `(0,0,0)` without warning. Log a warning.
- [ ] **Smithery registry card**: Minimal description — add proper metadata for discoverability.
- [ ] **Page range support**: Allow restricting replacements to specific page ranges.

## Done

_None yet._
