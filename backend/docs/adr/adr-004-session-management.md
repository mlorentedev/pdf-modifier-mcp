# ADR-004: Session Management — In-Memory with TTL

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu

## Context

The editing workflow requires maintaining state between upload, structure analysis, AI detection, user edits, and final download. The service is single-instance on a VPS.

## Decision

In-memory dict with session ID keys and configurable TTL (default 1 hour).

### Session State

```python
@dataclass
class Session:
    id: str                              # UUID4
    file_path: Path                      # Original PDF path
    modified_path: Path | None           # Modified PDF path (after replace)
    original_filename: str               # Original upload filename
    structure: PDFStructure | None       # Cached analysis result
    replacements: dict[str, str]         # Current replacement map
    ai_suggestions: AISuggestions | None # AI-detected fields
    created_at: datetime
    expires_at: datetime
```

### Session Lifecycle

```
Upload → Session created (TTL=1h)
    │
    ├── Analyze → structure cached
    ├── AI Detect → suggestions cached
    ├── Replace → modified PDF created
    ├── Download → stream file
    └── TTL expires → cleanup job deletes
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/pdf/upload` | Upload PDF, create session → `{session_id}` |
| GET | `/api/pdf/{id}/structure` | Get PDF structure (cached) |
| POST | `/api/pdf/{id}/replace` | Apply replacements |
| GET | `/api/pdf/{id}/download` | Download modified PDF |
| DELETE | `/api/pdf/{id}` | Delete session explicitly |
| POST | `/api/ai/{id}/detect` | AI field detection |
| POST | `/api/ai/{id}/classify` | Document classification |
| POST | `/api/ai/{id}/redact` | PII redaction |

### Concurrency

- `threading.Lock` on session dict for write operations
- Read operations are lock-free (dict read is atomic in CPython)
- FastAPI runs async handlers; session access via `anyio.to_thread.run_sync` for writes

## Consequences

- Fast (no DB overhead)
- Lost on server restart (acceptable for VPS; users just re-upload)
- Single-instance only (no session sharing across instances)
- Future: Redis for persistence + multi-instance if needed

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Redis | Persistence, TTL native, multi-instance | Extra dependency, overkill for single VPS | **Rejected** |
| SQLite | Persistent, queryable | Write lock contention, no built-in TTL | **Rejected** |
| JWT stateless | Scalable | Can't store PDF paths securely, complex | **Rejected** |
| Server-sent events only | No state needed | Can't manage file lifecycle | **Rejected** |
