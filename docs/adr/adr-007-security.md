# ADR-007: Security — Defense in Depth

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** pattern-secrets-security, pattern-nan-builders-gateway

## Context

The service handles file uploads (PDFs), calls external AI APIs with API keys, and serves content via HTTP. Threats include: API key leaks, path traversal, PDF injection, SSRF via AI tool calling, XSS, DoS via large uploads.

## Decision

Multi-layer security approach per `pattern-secrets-security`:

### Layer 1: Pre-commit Defense

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
```

### Layer 2: Upload Security

```python
def sanitize_filename(filename: str) -> str:
    """Strip path components and dangerous characters."""
    name = Path(filename).name  # Remove directory traversal
    safe = "".join(c for c in name if c.isalnum() or c in "._-")
    return safe or "upload.pdf"

def validate_pdf_header(content: bytes) -> bool:
    """Verify PDF magic bytes before processing."""
    return content[:5] == b"%PDF-"
```

- Max file size: 100 MB (configurable)
- PDF magic bytes validation
- Filename sanitization (no path traversal)
- Content-Type validation

### Layer 3: API Key Protection

- `NAN_API_KEY` as env var only, never in code or logs
- Structured logging with secrets filter
- Error responses never include API key

### Layer 4: AI Safety

- No user-controlled URLs passed to AI (SSRF prevention)
- AI responses parsed with strict schemas (Pydantic validation)
- Tool calling limited to predefined functions (no arbitrary code execution)

### Layer 5: HTTP Security Headers

```python
# FastAPI middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### Layer 6: CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),  # From env
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### Layer 7: Rate Limiting

- Per-IP upload rate limit (10 uploads/min)
- Per-session AI call limit (20 calls/session)
- Global concurrency cap (matches NaN Cloud limits)

## Consequences

- Defense in depth: multiple layers, no single point of failure
- Pre-commit hooks catch leaks before they reach git
- Upload validation prevents malicious PDFs
- Security headers protect against common web attacks

## Security Checklist (per release)

- [ ] `gitleaks` passes
- [ ] `pip-audit` no high/critical vulnerabilities
- [ ] `bandit` no high-severity issues
- [ ] No hardcoded secrets in codebase
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] File size limits enforced
- [ ] PDF magic bytes validated
