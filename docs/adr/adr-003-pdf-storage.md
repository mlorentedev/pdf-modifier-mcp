# ADR-003: PDF Storage — Filesystem with Session TTL

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu

## Context

Uploaded PDFs need temporary storage between upload, editing, analysis, and download. No database is needed for this scope. The service runs on a VPS as part of Kubelab.

## Decision

Use filesystem storage: `storage/{session_id}/{filename}` with configurable TTL (default 1 hour). A periodic cleanup job removes expired sessions.

### Structure

```
storage/
├── {session-id-1}/
│   ├── original.pdf          # Upload intacto
│   ├── modified.pdf          # PDF modificado (output)
│   └── structure.json        # PDFStructure cache (optional)
├── {session-id-2}/
│   └── ...
```

### Configuration

```python
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "1"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
```

### Cleanup

- Background task on FastAPI startup: `asyncio.create_task(cleanup_loop())`
- Runs every 10 minutes
- Deletes sessions older than TTL
- Logs deleted session IDs

## Consequences

- Simple, no external dependencies
- Sufficient for single-user / small team usage on VPS
- Filesystem-backed = fast local I/O
- Future: can migrate to S3/MinIO without changing core logic (StorageService interface)

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| SQLite | Structured, queryable | Overkill for file paths, write lock contention | **Rejected** |
| Redis | Fast, TTL native | Extra dependency, stores binary blobs poorly | **Rejected** |
| Object storage (S3) | Scalable, persistent | Overkill for VPS, adds complexity | **Rejected** |
| In-memory only | No disk I/O | Lost on restart, can't serve file downloads | **Rejected** |
