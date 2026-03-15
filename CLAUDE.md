# CLAUDE.md

Guidance for Claude/LLM agents working on the `pdf-modifier-mcp` repository.

## Project Overview
**PDF Modifier MCP** allows text modification in PDFs while preserving layout and fonts.
- **Stack**: Python 3.12+, PyMuPDF (fitz), Typer, FastMCP.
- **Structure**: `src/` (source), `tests/` (pytest), `.github/` (CI/CD).

## Command Palette (Makefile)

| Goal | Command | Description |
|------|---------|-------------|
| **Setup** | `make setup` | Install deps & pre-commit hooks |
| **Run MCP** | `make run-mcp` | Start local MCP server |
| **Run CLI** | `make run-cli ARGS="..."` | Run CLI locally |
| **Quality** | `make check` | Run Lint + Type + Test |
| **Lint** | `make lint` / `make format` | Check/Fix style with Ruff |
| **Test** | `make test` | Run pytest with coverage |
| **Build** | `make build` | Build distribution artifacts |

## Architecture

- **Core Layer** (`src/pdf_modifier_mcp/core/`):
  - `modifier.py`: Text replacement engine (two-pass: single-span + cross-span) and `batch_process()`.
  - `analyzer.py`: PDF parsing, structure extraction, font inspection, hyperlink inventory.
  - `models.py`: Pydantic schemas (contracts) — includes `BatchResult`.
  - `exceptions.py`: Typed exception hierarchy (`FileSizeExceededError`, `PDFNotFoundError`, etc.).
- **Interface Layer** (`src/pdf_modifier_mcp/interfaces/`):
  - `cli.py`: Typer-based command line.
  - `mcp.py`: FastMCP-based server.

## Workflow Rules

1.  **Commits**: Must follow [Conventional Commits](https://www.conventionalcommits.org/).
    - `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
2.  **Versioning**: Automated by Semantic Release based on commits.
    - Do **not** manually bump `pyproject.toml`.

## Common Tasks

### Adding a new MCP Tool
1.  Define the logic in `core/`.
2.  Expose it in `interfaces/mcp.py` using the `@mcp.tool()` decorator.
3.  Add a corresponding CLI command in `interfaces/cli.py` (feature parity).
4.  Add tests in `tests/`.

### Debugging
- Use `make run-cli ARGS="analyze file.pdf --json"` to inspect how the tool sees the PDF.
- Check `tests/examples_output/` for artifacts generated during tests.
