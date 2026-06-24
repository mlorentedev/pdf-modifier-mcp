---
id: "AI-001-verification"
type: spec-verification
status: pending
created: "2026-06-19"
---

# AI-001: Verification — AI Detection

## Verification Checklist

### Unit Tests
- [ ] All tests pass: `uv run pytest tests/test_ai/ -v`
- [ ] AI client tests use mocked httpx
- [ ] Router tests verify correct model selection
- [ ] Throttle tests verify concurrency limits
- [ ] Prompt rendering tests verify template output

### Integration Tests
- [ ] Detect endpoint returns valid DetectResult
- [ ] Classify endpoint returns valid document type
- [ ] Redact endpoint finds PII in test PDF
- [ ] AI calls use mocked responses in tests

### Security
- [ ] API key never logged
- [ ] API key never in error responses
- [ ] No user URLs passed to AI (SSRF prevention)
- [ ] AI responses validated with Pydantic

### AI Quality
- [ ] Detect returns meaningful fields for sample invoice
- [ ] Classify correctly identifies invoice vs contract
- [ ] Redact finds NIF, email, phone in test PDF
- [ ] Fallback works on simulated 429 error

### Performance
- [ ] AI call completes within 30 seconds
- [ ] Throttle prevents exceeding concurrency limit
- [ ] Rate limiting respects NaN Cloud limits

## Evidence

(Populated after implementation)

### Test Output
```
(Paste pytest output here)
```

### AI Response Samples
```
(Paste sample AI responses here)
```

## Lessons Learned

(Populated during implementation)

## PR Link

(Link to merged PR)
