---
id: "INFRA-001-tasks"
type: spec-tasks
status: active
created: "2026-06-19"
---

# INFRA-001: Tasks — Docker Infrastructure

## TDD Workflow

For infrastructure: verify build → verify run → verify health → verify compose.

---

## Phase 1: Backend Docker

### T1.1: Backend Dockerfile
- [ ] Create multi-stage Dockerfile
- [ ] Stage 1 (builder): python:3.12-slim, uv sync
- [ ] Stage 2 (runtime): python:3.12-slim, non-root user
- [ ] Copy venv and src from builder
- [ ] Add HEALTHCHECK instruction
- [ ] Test build: `docker build -t pdf-modifier-api .`
- [ ] Test run: `docker run -p 8000:8000 pdf-modifier-api`
- [ ] Verify health: `curl http://localhost:8000/health`

### T1.2: Backend Config
- [ ] Create `.dockerignore`
- [ ] Create `.env.example` with all variables
- [ ] Document env vars in README
- [ ] Test env var loading in container

---

## Phase 2: Frontend Docker

### T2.1: Frontend Dockerfile
- [ ] Create multi-stage Dockerfile
- [ ] Stage 1 (build): node:22-alpine, npm ci, npm run build
- [ ] Stage 2 (runtime): nginx:alpine, copy build output
- [ ] Test build: `docker build -t pdf-modifier-web ./apps/web`
- [ ] Test run: `docker run -p 3000:3000 pdf-modifier-web`
- [ ] Verify: `curl http://localhost:3000/`

### T2.2: Nginx Configuration
- [ ] Create nginx.conf for SPA routing
- [ ] Add API proxy to backend
- [ ] Add security headers
- [ ] Test SPA routing works

---

## Phase 3: Docker Compose

### T3.1: Base Compose
- [ ] Create `infra/compose.base.yml`
- [ ] Define api, web, nginx services
- [ ] Add volumes for storage
- [ ] Add health checks
- [ ] Test: `docker compose -f infra/compose.base.yml up`

### T3.2: Dev Compose
- [ ] Create `infra/compose.dev.yml`
- [ ] Add hot-reload for backend (uvicorn --reload)
- [ ] Add hot-reload for frontend (vite dev)
- [ ] Add debug ports
- [ ] Test: `docker compose -f base.yml -f dev.yml up`

### T3.3: Prod Compose
- [ ] Create `infra/compose.prod.yml`
- [ ] Remove debug options
- [ ] Add resource limits
- [ ] Add restart policies
- [ ] Test: `docker compose -f base.yml -f prod.yml up`

---

## Phase 4: CI/CD

### T4.1: Test Workflow
- [ ] Create `.github/workflows/test.yml`
- [ ] Run pytest with coverage
- [ ] Run mypy
- [ ] Run ruff
- [ ] Upload coverage to Codecov

### T4.2: Mutation Workflow
- [ ] Create `.github/workflows/mutation.yml`
- [ ] Run mutmut
- [ ] Check mutation score ≥70%
- [ ] Fail CI if score drops

### T4.3: Security Workflow
- [ ] Create `.github/workflows/security.yml`
- [ ] Run gitleaks
- [ ] Run pip-audit
- [ ] Run bandit
- [ ] Fail CI on high/critical issues

### T4.4: Build Workflow
- [ ] Create `.github/workflows/build.yml`
- [ ] Build backend Docker image
- [ ] Build frontend Docker image
- [ ] Test images run correctly
- [ ] Push to registry (on main branch)

---

## Phase 5: Pre-commit Hooks

### T5.1: Pre-commit Config
- [ ] Create/update `.pre-commit-config.yaml`
- [ ] Add gitleaks hook
- [ ] Add ruff hooks
- [ ] Add mypy hook
- [ ] Test: `pre-commit run --all-files`

---

## Dependencies

| Task | Depends on |
|---|---|
| T1.1-T1.2 | — |
| T2.1-T2.2 | — |
| T3.1-T3.3 | T1.1, T2.1 |
| T4.1-T4.4 | T1.1, T2.1 |
| T5.1 | — |

## Estimated Effort

| Phase | Tasks | Estimated LOC | Days |
|---|---|---|---|
| Phase 1: Backend Docker | T1.1-T1.2 | ~80 | 1 |
| Phase 2: Frontend Docker | T2.1-T2.2 | ~60 | 1 |
| Phase 3: Docker Compose | T3.1-T3.3 | ~100 | 1 |
| Phase 4: CI/CD | T4.1-T4.4 | ~150 | 1.5 |
| Phase 5: Pre-commit | T5.1 | ~30 | 0.5 |
| **Total** | **12 tasks** | **~420** | **~5** |
