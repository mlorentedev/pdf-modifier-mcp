# AGENTS.md

> Single source of truth for AI coding agents working on this repository.
> Replaces CLAUDE.md as the per-repo agent configuration.

## Project Overview

**PDF Modifier MCP** allows text modification in PDFs while preserving layout and fonts.

- **Stack**: Python 3.12+, PyMuPDF (fitz), Typer, FastMCP, Pydantic v2.
- **Version**: 1.4.2
- **License**: MIT
- **Vault**: `C:/Users/mlorente/Projects/Workspace/knowledge` (per-machine override in `~/.config/dotfiles/machine.json`)
- **Source**: `C:/Users/mlorente/Projects/Workspace/pdf-modifier-mcp`

## Architecture

```
src/pdf_modifier_mcp/
├── core/                    # SIN CAMBIOS — reutilizar tal cual
│   ├── modifier.py          # Text replacement engine (two-pass)
│   ├── analyzer.py          # PDF parsing, structure, fonts, hyperlinks
│   ├── models.py            # Pydantic schemas (contracts)
│   └── exceptions.py        # Typed exception hierarchy
├── ai/                      # NUEVO — AI Layer (Phase 2)
│   ├── client.py            # NaN Cloud API client (httpx, OpenAI-compatible)
│   ├── router.py            # TaskType → model routing
│   ├── throttle.py          # Rate limiter (semaphore-based)
│   ├── prompts/             # Jinja2 prompt templates
│   └── models.py            # AI-specific Pydantic models
├── web/                     # NUEVO — Web Layer (Phase 1)
│   ├── app.py               # FastAPI app factory
│   ├── routes/              # pdf.py, ai.py, health.py
│   ├── session.py           # Session manager (in-memory + TTL)
│   ├── storage.py           # PDF storage (filesystem)
│   ├── config.py            # Pydantic Settings
│   └── deps.py              # Dependency injection
├── interfaces/              # SIN CAMBIOS
│   ├── cli.py               # Typer CLI
│   └── mcp.py               # FastMCP server (5 tools)
└── logger.py
```

## Decision Hierarchy

1. **Correctness** > Performance > Elegance
2. **User Understanding** > Blind Implementation
3. **Stdlib** > Battle-tested libs > New dependencies
4. **Boring tech** > Cutting edge
5. **Explicit** > Implicit

## Standing Orders

1. **Core is sacred.** `core/modifier.py` and `core/analyzer.py` are NOT modified. New features call them as-is.
2. **TDD is mandatory.** RED → GREEN → REFACTOR for every task.
3. **Conventional commits.** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
4. **No manual version bumps.** Semantic Release handles versioning via commits.
5. **Specs before code.** Every feature >50 LOC needs `specs/<id>/` with proposal + tasks + verification.
6. **ADRs for decisions.** Non-reversible decisions go in `docs/adr/adr-XXX.md`.
7. **No secrets in code.** API keys via env vars only. `gitleaks` pre-commit hook enforced.
8. **Async-aware.** FastAPI is async; core is sync. Use `anyio.to_thread.run_sync` for core calls.

## Command Palette

| Goal | Command | Description |
|------|---------|-------------|
| **Setup** | `make setup` | Install deps & pre-commit hooks |
| **Run MCP** | `make run-mcp` | Start local MCP server |
| **Run CLI** | `make run-cli ARGS="..."` | Run CLI locally |
| **Run Web** | `make run-web` | Start FastAPI dev server |
| **Quality** | `make check` | Run Lint + Type + Test |
| **Lint** | `make lint` / `make format` | Check/Fix style with Ruff |
| **Test** | `make test` | Run pytest with coverage |
| **Mutation** | `make mutation` | Run mutmut mutation testing |
| **Build** | `make build` | Build distribution artifacts |
| **Docker** | `docker compose up` | Start all services |

## NaN Cloud Integration

- **Base URL**: `https://api.nan.builders/v1`
- **Auth**: `Authorization: Bearer $NAN_API_KEY`
- **Rate limits**: ~100 RPM / 5 concurrent (account-wide)
- **Always send**: `chat_template_kwargs: {"enable_thinking": false}`

### Model Routing

| Task | Model | Why |
|---|---|---|
| Vision / OCR | mimo-v2.5 | Only multimodal model |
| Tool calling | mimo-v2.5 | Native function calling |
| Reasoning | mimo-v2.5 | Reasoning mode, 1M context |
| Classification | qwen3.6 | Fast, cheap |
| Translation | qwen3.6 | Fast, 256K context |
| Summary | qwen3.6 | Fast |
| Embeddings | qwen3-embedding | Only embedding model |
| Rerank | rerank | Only reranking model |
| TTS | kokoro | Only TTS model |
| STT | whisper | Only STT model |

### Fallback Chain

```
mimo-v2.5 → qwen3.6 → gemma4
```

Fallback on: 429, 404, 5xx. Fail fast on: 400, 401.

## Testing Standards

- **Framework**: pytest + pytest-cov
- **Coverage**: ≥80% global, ≥90% critical paths
- **Mutation**: mutmut, score ≥70%
- **AI mocking**: NullAIClient for unit tests, never real API calls
- **File I/O**: `tmp_path` fixture, never write to real project dir
- **Naming**: `test_<unit>_<scenario>_<expected>`

## Security

- `gitleaks` pre-commit hook (mandatory)
- `bandit` for Python security linting
- `pip-audit` for dependency vulnerabilities
- Upload validation: PDF magic bytes, filename sanitization, max size
- CORS configured via env var
- Security headers on all responses

## Patterns Applied

| Pattern | Where |
|---|---|
| pattern-architecture | Monolith structure (core/ai/web/interfaces) |
| pattern-async-threading | anyio.to_thread for sync core |
| pattern-container-workflow | Multi-stage Docker, non-root, health checks |
| pattern-decision-persistence | ADRs in docs/adr/ |
| pattern-integration-testing | FastAPI TestClient + mocked AI |
| pattern-mcp-tool-design | MCP server preserved, <12 tools |
| pattern-nan-builders-gateway | Throttle, fallback, enable_thinking |
| pattern-python-cli | Typer CLI preserved |
| pattern-secrets-security | gitleaks, age, no secrets in code |
| pattern-spec-driven-development | specs/<id>/ per feature |
| pattern-testing-standards | TDD, mutation testing |
| pattern-workflow-protocol | Knowledge placement (ADRs → repo docs/) |
