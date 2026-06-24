# ADR-002: AI Layer — Centralized Service with Model Router + Throttle

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** pattern-nan-builders-gateway, pattern-async-threading

## Context

Multiple AI capabilities are needed (vision, tool calling, translation, embeddings, TTS, STT). Each requires different models from NaN Cloud. The API is OpenAI-compatible at `https://api.nan.builders/v1`.

Key constraints from NaN Cloud:
- Rate limits are account-wide (~100 RPM / 5 concurrent per account)
- `enable_thinking: false` must be sent in every request (burns quota + adds 3-10x latency otherwise)
- Reasoning models return non-standard `reasoning_content` field — ignore it, parse only `content`
- Fallback only on availability errors (429, 404, 5xx); fail fast on client errors (400, 401)

## Decision

Centralize all AI interactions in a `core/ai/` layer with:

### Components

1. **`client.py`** — httpx-based async HTTP client for NaN Cloud
   - OpenAI-compatible request/response format
   - SSE streaming support
   - `enable_thinking: false` in every request

2. **`router.py`** — `TaskType` enum → model routing
   - Default mapping per task type
   - Config override via env var or constructor

3. **`throttle.py`** — Rate limiter
   - Semaphore-based concurrency cap (default 3, env-overridable)
   - Per-model RPM tracking
   - Backoff on 429

4. **`prompts/`** — Jinja2 prompt templates per task type

### Model Routing (default)

| TaskType | Model | Reason |
|---|---|---|
| `VISION` | mimo-v2.5 | Only model with native multimodal vision |
| `TOOL_CALLING` | mimo-v2.5 | Native function calling support |
| `REASONING` | mimo-v2.5 | Reasoning mode, 1M context |
| `CLASSIFICATION` | qwen3.6 | Fast, cheap, sufficient |
| `TRANSLATION` | qwen3.6 | Fast, good quality, 256K context |
| `SUMMARY` | qwen3.6 | Fast |
| `EMBEDDING` | qwen3-embedding | Only embedding model |
| `RERANK` | rerank | Only reranking model |
| `TTS` | kokoro | Only TTS model |
| `STT` | whisper | Only STT model |

### Fallback Chain

```
Throttle(
    FallbackChain(
        mimo-v2.5 → qwen3.6 → gemma4
    )
)
```

Fallback triggers: HTTP 429, 404, 5xx, network/timeout.
Fail fast: HTTP 400, 401 (deterministic errors).

### Concurrency Model

```python
# Async client, sync core wrapped in thread
async def ai_detect_fields(pdf_bytes: bytes) -> DetectResult:
    async with semaphore:  # max 3 concurrent
        response = await client.chat.completions.create(
            model=router.get_model(TaskType.TOOL_CALLING),
            messages=[...],
            tools=[...],
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
    return parse_response(response)
```

## Consequences

- Single point for rate limiting, retry, and fallback
- Easy to swap models or add new providers
- Prompts are version-controlled and testable
- `core/` layer can be tested independently (mock the HTTP client)
- Throttle respects NaN Cloud account-wide limits

## NaN Cloud Model Reference

| Model | Params | Context | Modalities | RPM (tpm) | Use case |
|---|---|---|---|---|---|
| mimo-v2.5 | 310B/15B | 1M | text+image+audio | 1.5M | Vision, tool calling, reasoning |
| qwen3.6 | 35B/3B | 256K | text+image | 1.5M | Translation, summary, fast tasks |
| gemma4 | 26B/4B | 256K | text+image | 1.5M | Fallback, lightweight |
| qwen3-embedding | 8B | — | text | 60 RPM | Embeddings (4096 dim) |
| rerank | 8B | — | text | 1000 RPM | Reranking |
| kokoro | 82M | — | text→audio | 15 RPM | TTS (67 voices) |
| whisper | large-v3 | — | audio→text | 10 RPM | STT (99+ languages) |

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Distributed tools (each tool calls AI directly) | Simpler per tool | DRY violation, no central rate limiting, model hardcoded | **Rejected** |
| OpenAI Python SDK | Well-known | Adds dependency, less control over `enable_thinking` flag | **Rejected** |
| LiteLLM | Multi-provider abstraction | Overkill for single provider (NaN), adds latency | **Rejected** |
