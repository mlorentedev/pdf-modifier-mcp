# pdf-modifier-mcp — Backlog

> MCP server + CLI for PDF text replacement with style preservation.

## P0 — High Priority

- [ ] **File size validation**: No max file size check before processing. Large PDFs could cause OOM.
- [ ] **Multi-span regex matching** ([#4](https://github.com/mlorentedev/pdf-modifier-mcp/issues/4)): Match text across span boundaries using span-merging logic.
- [ ] **Batch processing support** ([#11](https://github.com/mlorentedev/pdf-modifier-mcp/issues/11)): Process multiple PDFs in a single invocation (directory mode or glob pattern).

## P1 — Medium Priority

- [ ] **Preview modification tool** ([#10](https://github.com/mlorentedev/pdf-modifier-mcp/issues/10)): Dry-run mode showing what would change without writing.
- [ ] **Table extraction to JSON** ([#7](https://github.com/mlorentedev/pdf-modifier-mcp/issues/7)): Extract tabular data from PDFs as structured JSON.
- [ ] **Metadata read/write** ([#9](https://github.com/mlorentedev/pdf-modifier-mcp/issues/9), [#14](https://github.com/mlorentedev/pdf-modifier-mcp/issues/14)): Read and edit PDF metadata (title, author, keywords).
- [ ] **PDF sanitization** ([#12](https://github.com/mlorentedev/pdf-modifier-mcp/issues/12)): Strip hidden data, metadata, and embedded objects for security.
- [ ] **Expose PDFs as MCP resources** ([#15](https://github.com/mlorentedev/pdf-modifier-mcp/issues/15)): Use MCP resource protocol for PDF file access.
- [ ] **Add MCP standard prompts** ([#16](https://github.com/mlorentedev/pdf-modifier-mcp/issues/16)): Pre-built prompt templates for common workflows.
- [ ] **Programmatic API examples in README**: Add Python library usage examples.
- [ ] **Test large PDFs**: Performance/memory tests for documents with many pages.

## P2 — Low Priority / Nice-to-Have

- [ ] **CMYK and Grayscale color spaces** ([#6](https://github.com/mlorentedev/pdf-modifier-mcp/issues/6)): Support non-RGB color models.
- [ ] **Image replacement** ([#5](https://github.com/mlorentedev/pdf-modifier-mcp/issues/5)): Replace images in PDFs.
- [ ] **Advanced font support** ([#3](https://github.com/mlorentedev/pdf-modifier-mcp/issues/3)): Custom font paths and non-Base14 embedding.
- [ ] **Text reflow and layout management** ([#2](https://github.com/mlorentedev/pdf-modifier-mcp/issues/2)): Handle text that exceeds original bounding box.
- [ ] **Font width caching**: Cache font widths for repeated same-font replacements.
- [ ] **Silent color fallback**: Log a warning when invalid color defaults to black.
- [ ] **Page range support**: Restrict replacements to specific page ranges.

## Done

- [x] ~~**Cross-span text matching**~~: Documented as known limitation in troubleshooting guide + test proving behavior.
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
