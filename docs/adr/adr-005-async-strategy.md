# ADR-005: Async Strategy — anyio.to_thread for Sync Core

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** pattern-async-threading

## Context

FastAPI is async-native. The existing core (`PDFModifier`, `PDFAnalyzer`) is synchronous (PyMuPDF/fitz is blocking). AI calls via httpx are async. Mixing these requires careful thread management to avoid blocking the event loop.

## Decision

### Layer 1: FastAPI async handlers

All route handlers are `async def`. No blocking calls in the handler body.

### Layer 2: Core wrapped in thread pool

```python
import anyio

@app.post("/api/pdf/{session_id}/replace")
async def replace_text(session_id: str, spec: ReplacementSpec) -> ModificationResult:
    session = session_manager.get(session_id)
    # Core is sync → run in thread pool to avoid blocking event loop
    result = await anyio.to_thread.run_sync(
        _process_pdf_sync, session.file_path, spec
    )
    return result

def _process_pdf_sync(path: Path, spec: ReplacementSpec) -> ModificationResult:
    """Sync function — runs in thread pool."""
    modifier = PDFModifier(path, path.with_suffix(".modified.pdf"))
    return modifier.process(spec)
```

### Layer 3: AI calls are async (httpx)

```python
async def call_nan_api(messages: list[dict], model: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.nan.builders/v1/chat/completions",
            json={"model": model, "messages": messages},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        return response.json()["choices"][0]["message"]["content"]
```

### Layer 4: Storage writes use threading.Lock

```python
import threading

_STORAGE_LOCK = threading.Lock()

def save_pdf(session_id: str, content: bytes) -> Path:
    if not _STORAGE_LOCK.acquire(timeout=30):
        raise HTTPException(503, "Storage busy, try again")
    try:
        path = STORAGE_DIR / session_id / "modified.pdf"
        path.write_bytes(content)
        return path
    finally:
        _STORAGE_LOCK.release()
```

### Timeout Layers

| Layer | Mechanism | Timeout |
|---|---|---|
| FastAPI request | `asyncio.timeout` | 300s (5 min) |
| Core processing | `anyio.to_thread.run_sync` | 120s (2 min) |
| AI API call | `httpx.Timeout` | 60s |
| Storage write | `Lock.acquire(timeout=)` | 30s |

## Consequences

- Event loop never blocked by sync core
- AI calls are properly async (non-blocking)
- File I/O is serialized via Lock (prevents race conditions)
- Thread pool size controlled by uvicorn worker config

## Anti-Patterns Avoided

- ❌ `asyncio.timeout()` around threaded work (can't interrupt blocked threads)
- ❌ `await` on sync fitz calls (would block event loop)
- ❌ Unprotected file read-modify-write (TOCTOU race condition)
