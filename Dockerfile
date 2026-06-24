# =============================================================================
# Backend Dockerfile — pdf-modifier-mcp (FastAPI)
# Multi-stage: builder (download wheels) → runtime (install + run, non-root)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — download wheels to avoid network in runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Copy dependency specs first (layer caching)
COPY pyproject.toml uv.lock ./

# Install pip and use pip wheel to download all deps
RUN pip install --no-cache-dir uv && \
    uv pip compile pyproject.toml --python-version 3.12 -q -o requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime — minimal image, non-root user
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy everything before installing (pip install needs pyproject.toml)
COPY pyproject.toml ./
COPY src/ ./
COPY server.json ./
COPY CHANGELOG.md LICENSE README.md ./

# Create a fresh venv (shebangs point here)
RUN python -m venv /app/.venv

# Install wheels from builder (no network needed)
COPY --from=builder /wheels /wheels
RUN /app/.venv/bin/pip install --no-cache-dir /wheels/* && rm -rf /wheels && \
    /app/.venv/bin/pip install --no-cache-dir .

# Create runtime directories and set ownership before switching user
RUN mkdir -p /app/.pdf-modifier/logs /app/storage && chown -R appuser:appuser /app

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD /app/.venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Switch to non-root user
USER appuser

# Default command: run FastAPI via uvicorn
CMD ["/app/.venv/bin/uvicorn", "pdf_modifier.web.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
