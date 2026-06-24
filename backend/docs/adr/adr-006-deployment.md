# ADR-006: Deployment — Docker on VPS (Kubelab)

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** pattern-container-workflow

## Context

The service will run on Manu's VPS as part of Kubelab infrastructure. It needs to coexist with other services, support HTTPS, and be deployable via Docker Compose.

## Decision

Multi-container Docker Compose deployment on VPS, behind Kubelab's existing reverse proxy (Traefik).

### Container Architecture

```
┌─────────────────────────────────────────────────┐
│            Kubelab VPS (Docker Compose)          │
│                                                   │
│  ┌──────────────┐  ┌──────────────┐              │
│  │   web        │  │   api        │              │
│  │   SvelteKit  │  │   FastAPI    │              │
│  │   :3000      │  │   :8000      │              │
│  └──────────────┘  └──────────────┘              │
│         │                 │                       │
│         └────────┬────────┘                       │
│                  │                                │
│         ┌────────┴────────┐                       │
│         │   Traefik       │ ← existing           │
│         │   reverse proxy │   Kubelab proxy      │
│         │   :80/:443      │                       │
│         └─────────────────┘                       │
└─────────────────────────────────────────────────┘
```

### Dockerfile Strategy (Multi-Stage)

**Backend:**
- Stage 1 (builder): `python:3.12-slim`, install deps with `uv`
- Stage 2 (runtime): `python:3.12-slim`, non-root user, copy venv + src

**Frontend:**
- Stage 1 (build): `node:22-alpine`, `npm ci && npm run build`
- Stage 2 (runtime): `nginx:alpine`, serve static files

### Compose Files

```
infra/
├── compose.base.yml        # Shared config (images, volumes)
├── compose.dev.yml         # Dev overrides (hot-reload, debug)
├── compose.prod.yml        # Prod overrides (no debug, health checks)
└── .env.example            # Template
```

### Volumes

- `pdf-storage` — named volume for uploaded/modified PDFs
- Bind mount for nginx config in dev

### Health Checks

```yaml
api:
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval: 30s
    timeout: 10s
    retries: 3

web:
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:3000/"]
    interval: 30s
    timeout: 5s
    retries: 3
```

### Environment Variables

```bash
# Required
NAN_API_KEY=sk-...
STORAGE_DIR=/app/storage

# Optional (with defaults)
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
MAX_FILE_SIZE_MB=100
SESSION_TTL_HOURS=1
MAX_SESSIONS=50
AI_THROTTLE_CONCURRENCY=3
```

### Secrets Management

Per `pattern-secrets-security`:
- `.env` file on VPS (NOT committed to git)
- `gitleaks` pre-commit hook prevents accidental commits
- `NAN_API_KEY` loaded from env, never hardcoded

## Consequences

- Coexists with existing Kubelab services via Traefik
- Multi-stage builds keep images small (~150MB backend, ~50MB frontend)
- Health checks enable Docker's restart policy
- Secrets never in image layers

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| NaN Cloud Apps | Zero-config deploy | Beta, no control, can't coexist with Kubelab | **Rejected** |
| Kubernetes (K3s) | More features | Overkill for single VPS, operational complexity | **Rejected** |
| Single container | Simpler | Can't scale frontend/backend independently | **Rejected** |
| Venv on bare metal | No Docker overhead | No isolation, harder to reproduce | **Rejected** |
