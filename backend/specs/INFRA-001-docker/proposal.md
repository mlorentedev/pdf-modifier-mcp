---
id: "INFRA-001"
type: spec
status: active
created: "2026-06-19"
feature: Docker Infrastructure
---

# INFRA-001: Docker Infrastructure

## What

Create Docker infrastructure for the project: multi-stage Dockerfiles for backend and frontend, Docker Compose for local development and production, nginx configuration for reverse proxy, and CI/CD pipelines.

## Why

- Consistent development environment
- Reproducible builds
- Easy deployment to VPS (Kubelab)
- Isolation from host system
- Health checks for monitoring

## Scope

### In Scope
- Backend Dockerfile (FastAPI, multi-stage)
- Frontend Dockerfile (SvelteKit, multi-stage)
- docker-compose.base.yml
- docker-compose.dev.yml (hot-reload)
- docker-compose.prod.yml
- nginx configuration
- CI/CD workflows (test, mutation, security, build)
- Health check endpoints

### Out of Scope
- Kubernetes deployment (VPS uses Docker Compose)
- CI/CD to production (manual deploy for now)
- Monitoring/alerting (basic health checks only)

## Acceptance Criteria

1. [ ] Backend builds and runs in Docker
2. [ ] Frontend builds and runs in Docker
3. [ ] Compose starts all services
4. [ ] Health checks pass
5. [ ] Dev mode has hot-reload
6. [ ] Production mode is optimized
7. [ ] CI runs tests and security scans
8. [ ] No secrets in Docker images

## Technical Notes

- ADR-006: Deployment architecture
- `pattern-container-workflow`: Multi-stage, non-root, health checks
- `pattern-secrets-security`: No secrets in images
- Multi-arch: linux/amd64 for VPS
