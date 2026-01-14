# Testing Guide

Step-by-step manual testing checklist for PDF Modifier MCP.

---

## 1. Local Setup

```bash
make setup
```

**Expected:**
```
✓ Dependencies installed
✓ Pre-commit hooks installed
✓ Setup complete. Run 'make run-mcp' to start.
```

---

## 2. Version Check

```bash
poetry version
```

**Expected:**
```
pdf-modifier-mcp 0.0.1
```

---

## 3. Quality Checks

```bash
make check
```

**Expected:**
```
✓ All checks passed
```

---

## 4. CLI Help

```bash
make cli ARGS="--help"
```

**Expected:**
```
Usage: pdf-mod [OPTIONS] COMMAND [ARGS]...
...
Commands:
  analyze   Analyze PDF structure and extract text content.
  inspect   Inspect font properties for specific terms in a PDF.
  modify    Modify text in a PDF file with find/replace operations.
```

---

## 5. Demo: Analyze PDF

```bash
poetry run pdf-mod analyze tests/data/sample.pdf --json
```

**Expected:** JSON output with PDF structure:
```json
{
  "file_path": "tests/data/sample.pdf",
  "total_pages": 1,
  "pages": [...]
}
```

---

## 6. Demo: Inspect Fonts

```bash
poetry run pdf-mod inspect tests/data/sample.pdf the
```

**Expected:** Table with font matches for "the".

---

## 7. Demo: Modify PDF

```bash
poetry run pdf-mod modify tests/data/sample.pdf tests/data/output.pdf -r "Manuel Lorente=John Doe"
```

**Expected:**
```
Success: Saved to .../tests/data/output.pdf
```

Verify output:
```bash
ls -la tests/data/output.pdf
```

---

## 8. Docker Build

```bash
make docker-build
```

**Expected:**
```
...
✓ Built and tagged pdf-modifier-mcp:0.0.1 and pdf-modifier-mcp:latest
```

---

## 9. Docker CLI

```bash
docker run --rm --entrypoint pdf-mod -v $(pwd)/tests/data:/data pdf-modifier-mcp:latest --help
```

**Expected:** Same help output as step 4.

---

## 10. Docker Demo

```bash
docker run --rm --entrypoint pdf-mod -v $(pwd)/tests/data:/data pdf-modifier-mcp:latest analyze /data/sample.pdf --json
```

**Expected:** Same JSON output as step 5.

---

## 11. MCP Inspector (Optional)

```bash
npx @modelcontextprotocol/inspector poetry run pdf-modifier-mcp
```

**Expected:**
- Browser opens at `http://localhost:5173`
- Tools available: `read_pdf_structure`, `inspect_pdf_fonts`, `modify_pdf_content`

---

## 12. Pre-commit Hooks

```bash
poetry run pre-commit run --all-files
```

**Expected:** All hooks passed.

---

## 13. Git Commit (Conventional)

```bash
git add .
git commit -m "feat: test semantic release workflow"
```

**Expected:** Pre-commit hooks pass, commit successful.

---

## 14. Release Verification

1. Push branch: `git push -u origin feat/test`
2. Create PR.
3. Verify CI passes.
4. Merge PR.
5. Verify new release tag (v0.1.0) and PyPI publish.

---

*Last Updated: 2026-01-13*
