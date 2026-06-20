# ADR-011: Semantic Search — Embedding + Rerank Pipeline

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** ADR-002 (AI Layer), ML-001

## Context

Semantic search allows users to find concepts in PDFs, not just exact text. Requires:
- Embedding PDF text elements into vectors
- Embedding user query
- Computing similarity
- Reranking for precision

Key questions:
- Where to store embeddings? (in-session vs external DB)
- When to compute? (on-demand vs pre-computed)
- How to handle large PDFs? (many text elements)

## Decision

### Architecture

```
User Query → Embed query (qwen3-embedding)
                    ↓
            Cosine similarity against cached embeddings
                    ↓
            Top-K candidates (K=20)
                    ↓
            Rerank with rerank model
                    ↓
            Top-N results (N=10)
```

### Embedding Strategy

- **Compute:** On-demand when user first requests search
- **Cache:** In session storage (`embeddings.json`)
- **Model:** qwen3-embedding (4096 dim, FP32)
- **Batch size:** 32 (API limit)
- **Text chunking:** Each `TextElement` from PDFStructure is embedded as-is

### Storage

```json
// session storage/embeddings.json
{
  "page_1": {
    "0": [0.12, -0.34, ...],  // 4096 floats
    "1": [0.56, 0.78, ...],
    ...
  },
  "page_2": { ... }
}
```

- Stored per-session (same TTL as session)
- No external database needed
- Computed once, reused for multiple queries

### Search Pipeline

```python
async def semantic_search(session_id: str, query: str) -> list[SearchResult]:
    # 1. Load cached embeddings
    embeddings = load_embeddings(session_id)

    # 2. Embed query (single API call)
    query_embedding = await embedding_client.get_embedding(query)

    # 3. Compute cosine similarity (in-memory, fast)
    scores = cosine_similarity(query_embedding, embeddings)

    # 4. Get top-K candidates
    top_k = sorted(scores, key=scores.get, reverse=True)[:20]

    # 5. Rerank with rerank model
    reranked = await rerank_client.rerank(query, top_k)

    # 6. Return top-N
    return reranked[:10]
```

### Cosine Similarity

- Pure Python, no external dependencies
- `numpy.dot` if numpy available, else manual implementation
- In-memory computation (fast for <10K vectors)

### Cost Estimation

```
PDF with 500 text elements:
  - Embedding: 500/32 = 16 batch calls ≈ 16 RPM
  - Per search: 1 query embed + 1 rerank = 2 API calls
  - Total: 16 (one-time) + 2 (per search) API calls
```

## Consequences

- Embeddings computed once per session, reused for all searches
- No external vector DB needed (in-session scope)
- Cosine similarity is O(n) but fast for <10K vectors
- Rerank adds precision at cost of 1 extra API call

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Pre-compute on upload | Always ready | Wastes tokens if user never searches | **Rejected** |
| External vector DB (Chroma) | Persistent, fast | Extra dependency, overkill for single-PDF | **Rejected** |
| On-demand (no cache) | No storage | Recomputes every search, burns tokens | **Rejected** |
| TF-IDF (no embeddings) | No API calls | Poor semantic understanding | **Rejected** |
