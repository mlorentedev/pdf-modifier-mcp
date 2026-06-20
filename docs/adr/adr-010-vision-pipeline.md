# ADR-010: Vision Pipeline — PDF to Image to mimo-v2.5

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** ADR-002 (AI Layer), VIS-001

## Context

Vision capabilities (OCR, signature detection, PDF comparison) require converting PDF pages to images and sending them to mimo-v2.5. Key questions:
- How many pages to send? (1M context but image tokens are expensive)
- What resolution? (quality vs token cost)
- How to cache? (avoid re-rendering same pages)
- How to handle multi-page PDFs? (batch or stream)

## Decision

### Image Conversion

- **Format:** PNG (lossless, best for OCR)
- **DPI:** 150 (configurable, default 150 — good balance quality/tokens)
- **Source:** fitz `page.get_pixmap(dpi=150)`

### Page Selection Strategy

| Use Case | Pages Sent | Why |
|---|---|---|
| OCR (full document) | All pages, batched | Need complete text |
| Signature detection | All pages | Signatures can be anywhere |
| PDF comparison | Same pages from both | Must compare equivalent pages |
| Quick preview | First 3 pages | Fast feedback, user can expand |

### Batching

- **Max pages per request:** 10 (configurable)
- **Reason:** mimo-v2.5 has 1M context but image tokens are ~1000 tokens/page at 150 DPI. 10 pages = ~10K tokens, well within limits.
- **Multi-page PDFs:** Process in batches of 10, concatenate results.

### Caching

```python
# Cache key: (session_id, page_num, dpi)
# Cache value: image bytes (PNG)
# Location: session storage directory
# TTL: same as session (1 hour)
```

- Cache rendered images per session
- Avoids re-rendering when user requests same page multiple times
- Cache invalidated when session expires

### Token Estimation

```
1 page @ 150 DPI PNG ≈ 800-1200 tokens (mimo-v2.5 vision encoding)
10 pages ≈ 8K-12K tokens
100 pages (batched) ≈ 80K-120K tokens total
```

## Consequences

- 150 DPI is sufficient for OCR and signature detection
- Batching prevents token overflow
- Caching avoids redundant rendering
- PNG format ensures lossless quality for AI analysis

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| JPEG (lossy) | Smaller files | Artifacts hurt OCR accuracy | **Rejected** |
| 300 DPI | Higher quality | 4x tokens, slower, unnecessary for AI | **Rejected** |
| 72 DPI | Fewer tokens | Too low for OCR, blurry signatures | **Rejected** |
| Vector DB for embeddings | Persistent, fast search | Overkill for single-PDF scope | **Rejected** |
