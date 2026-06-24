---
id: "WEB-001-verification"
type: spec-verification
status: pending
created: "2026-06-19"
---

# WEB-001: Verification — Web UI

## Verification Checklist

### Unit Tests
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] Coverage ≥80%: `uv run pytest --cov=src --cov-fail-under=80`
- [ ] No mypy errors: `uv run mypy src/`
- [ ] No ruff errors: `uv run ruff check src/ tests/`

### Integration Tests
- [ ] Upload flow works end-to-end
- [ ] Structure endpoint returns valid data
- [ ] Replace endpoint modifies PDF correctly
- [ ] Download endpoint returns valid PDF
- [ ] Session expires after TTL
- [ ] Cleanup job removes expired sessions

### Security
- [ ] `gitleaks` passes
- [ ] `pip-audit` no high/critical vulnerabilities
- [ ] `bandit` no high-severity issues
- [ ] Upload validates PDF magic bytes
- [ ] Filename sanitization prevents path traversal
- [ ] CORS configured correctly
- [ ] Security headers present

### Mutation Testing
- [ ] `mutmut run` completes
- [ ] Mutation score ≥70%

### Docker
- [ ] Backend builds: `docker build -t pdf-modifier-api .`
- [ ] Frontend builds: `docker build -t pdf-modifier-web ./apps/web`
- [ ] Compose starts: `docker compose up -d`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Frontend accessible: `curl http://localhost:3000/`

### Manual Testing
- [ ] Drag-and-drop upload works
- [ ] Structure displays correctly
- [ ] Replacement form works
- [ ] PDF preview renders
- [ ] Download provides correct file
- [ ] Large PDF (>10MB) handles gracefully
- [ ] Session cleanup works

### Code Quality
- [ ] No `T | None` in MCP tool params (pattern-mcp-tool-design)
- [ ] All ADRs referenced correctly
- [ ] README updated
- [ ] API docs auto-generated

## Evidence

(Populated after implementation)

### Test Output
```
(Paste pytest output here)
```

### Coverage Report
```
(Paste coverage report here)
```

### Mutation Score
```
(Paste mutmut results here)
```

### Docker Build
```
(Paste docker build output here)
```

## Lessons Learned

(Populated during implementation)

## PR Link

(Link to merged PR)

## Promoted Artifacts

- [ ] Lesson → `docs/lessons.md`
- [ ] ADR → `docs/adr/`
- [ ] Pattern → `00_meta/patterns/`
