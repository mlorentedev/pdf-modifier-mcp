# Audit Report — Pre-Implementation

> Date: 2026-06-20
> Scope: Security, usability, code cleanliness before Phase 1 implementation

## Executive Summary

| Category | Status | Issues |
|---|---|---|
| **Security** | ⚠️ Medium | 2 issues found |
| **Code Quality** | ✅ Good | ruff ✅, mypy ✅, 132 tests pass |
| **Gitignore** | ❌ Missing entries | 5 entries missing |
| **Code Complexity** | ⚠️ Moderate | 1 function >100 lines |
| **Dependencies** | ✅ Clean | No known vulnerabilities |
| **Documentation** | ✅ Complete | ADRs, specs, README current |

---

## 1. Security Findings

### 🔴 CRITICAL: Missing .gitignore entries

| Pattern | Risk | Status |
|---|---|---|
| `.env` | API keys could be committed | ❌ NOT covered |
| `storage/` | User-uploaded PDFs could be committed | ❌ NOT covered |
| `*.pdf` | Test/example PDFs could be committed | ❌ NOT covered |
| `sensitive/` | Encrypted secrets could be committed | ❌ NOT covered |
| `nul` | Windows artifact (was committed earlier) | ❌ NOT covered |

**Fix:** Add to `.gitignore`:
```
# Environment
.env
.env.local
.env.*.local

# Storage (user uploads)
storage/

# PDFs (except test data)
*.pdf
!tests/data/*.pdf

# Sensitive
sensitive/

# Windows artifacts
nul
```

### 🟡 MEDIUM: No path traversal protection in core

The core `PDFModifier` and `PDFAnalyzer` accept `file_path` as `str | Path` and open it directly. If called from the web layer with user-controlled input, this could allow reading arbitrary files.

**Current state:** Core is only called by CLI/MCP (trusted input). Web layer (Phase 1) MUST add `sanitize_filename()` before passing to core.

**Recommendation:** ADR-007 covers this, but the web layer implementation must enforce it.

### 🟡 MEDIUM: Regex DoS potential

`ReplacementSpec` accepts user-provided regex patterns. Malicious patterns (e.g., `(a+)+$`) could cause catastrophic backtracking.

**Current state:** No timeout on regex compilation or matching.

**Recommendation:** Add `re.compile(pattern, re.TIMEOUT)` or a watchdog timer in Phase 1 web layer.

---

## 2. Code Quality

### ✅ Passing

| Check | Result |
|---|---|
| `ruff check` | All checks passed |
| `mypy --strict` | Success: no issues |
| `pytest` | 132 passed in 15.32s |
| Coverage | ≥80% (enforced in CI) |

### ⚠️ Function Length

| Function | Lines | Threshold | Status |
|---|---|---|---|
| `_match_across_spans` | 114 | 40 | ❌ Over limit |
| `process` | 75 | 40 | ❌ Over limit |
| `_collect_replacements` | 63 | 40 | ❌ Over limit |
| `batch_process` | 56 | 40 | ❌ Over limit |

**Recommendation:** Refactor `_match_across_spans` into smaller helpers. This is existing tech debt, not blocking Phase 1.

### ✅ No Dangerous Patterns

| Pattern | Status |
|---|---|
| `eval()` / `exec()` | ✅ Not found |
| `subprocess` | ✅ Not found |
| Hardcoded secrets | ✅ Not found |
| SQL queries | ✅ Not applicable |
| `pickle.load` | ✅ Not found |

---

## 3. Usability

### ✅ README

- Badges: CI, PyPI, Codecov, Python version, Docs, License
- Quick install for 4 tools (Claude, Gemini, Codex, Copilot)
- Command reference table
- Architecture diagram
- Before/after comparison

### ✅ CLI

- 5 commands: modify, batch, analyze, inspect, links
- Rich output (tables, colors)
- Help text on all commands
- `--json` flag for machine output

### ✅ MCP

- 5 tools with comprehensive docstrings
- JSON error responses
- Error handling decorator

### ⚠️ Missing: `make run-web` target

Makefile doesn't have a `run-web` target for the upcoming FastAPI server. Not blocking (Phase 1 will add it), but worth noting.

---

## 4. Dependency Audit

### Production Dependencies

| Package | Version Constraint | Risk |
|---|---|---|
| pymupdf | >=1.26.7 | ✅ Active, well-maintained |
| typer[all] | >=0.9.0 | ✅ Stable |
| fastmcp | >=0.4.1 | ✅ Active |
| pydantic | >=2.0.0 | ✅ Stable, widely used |

### Dev Dependencies

| Package | Version Constraint | Risk |
|---|---|---|
| pytest | >=7.0.0 | ✅ Stable |
| pytest-cov | >=4.0.0 | ✅ Stable |
| mypy | >=1.0.0 | ✅ Active |
| ruff | >=0.1.0 | ✅ Active |
| pre-commit | >=4.0.0 | ✅ Active |

### Missing (needed for Phase 1)

| Package | Purpose | Priority |
|---|---|---|
| fastapi | Web framework | Phase 1 |
| uvicorn[standard] | ASGI server | Phase 1 |
| python-multipart | File uploads | Phase 1 |
| aiofiles | Async file I/O | Phase 1 |
| httpx | Async HTTP client | Phase 2 |
| tenacity | Retry/backoff | Phase 2 |
| pytest-asyncio | Async test support | Phase 1 |

---

## 5. Gitignore Fix

**Immediate action required:** Add missing entries to `.gitignore`.

```diff
# Project Specific
tests/examples_output/
!tests/data/sample.pdf
*.log
.DS_Store
tests/examples_output/
data/

+# Environment
+.env
+.env.local
+.env.*.local
+
+# Storage (user uploads)
+storage/
+
+# PDFs (except test data)
+*.pdf
+!tests/data/*.pdf
+
+# Sensitive
+sensitive/
+
+# Windows artifacts
+nul

# AI
.claude/
.gemini/
```

---

## 6. Recommendations (Priority Order)

| # | Action | Priority | Blocks Phase 1? |
|---|---|---|---|
| 1 | Fix `.gitignore` (add .env, storage/, *.pdf, sensitive/, nul) | 🔴 Critical | No, but risky without it |
| 2 | Add regex timeout in web layer (Phase 1) | 🟡 Medium | Yes |
| 3 | Add path traversal protection in web upload (Phase 1) | 🟡 Medium | Yes |
| 4 | Refactor `_match_across_spans` (tech debt) | 🟢 Low | No |
| 5 | Add `make run-web` target (Phase 1) | 🟢 Low | Phase 1 will add |
| 6 | Install bandit for security scanning | 🟢 Low | No |

---

## Verdict

**The repo is in good shape for Phase 1 implementation.** The core is solid, tests pass, and the architecture is well-documented. The main action item is fixing `.gitignore` before any new code is written, and ensuring the web layer (Phase 1) implements the security measures documented in ADR-007.
