# Multi-stage Dockerfile for pdf-modifier-mcp
# Security-hardened with non-root user and minimal attack surface

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install poetry
RUN pip install --no-cache-dir poetry==2.2.1 && \
    poetry self add poetry-plugin-export

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt (without dev deps)
RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt

# Build wheel
COPY src/ src/
COPY README.md ./
RUN poetry build -f wheel

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

# Security hardening
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd --gid 1000 pdfmod \
    && useradd --uid 1000 --gid 1000 --shell /sbin/nologin --create-home pdfmod

WORKDIR /app

# Install runtime dependencies only
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

# Install the wheel
COPY --from=builder /build/dist/*.whl .
RUN pip install --no-cache-dir *.whl \
    && rm *.whl

# Create data directories with proper permissions
RUN mkdir -p /data \
    && chown -R pdfmod:pdfmod /data

# Remove unnecessary files
RUN rm -rf /root/.cache /tmp/* /var/tmp/*

# Switch to non-root user
USER pdfmod

WORKDIR /data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from pdf_modifier_mcp.core import PDFModifier; print('ok')" || exit 1

ENTRYPOINT ["pdf-modifier-mcp"]

# OCI Labels
LABEL org.opencontainers.image.title="pdf-modifier-mcp" \
      org.opencontainers.image.description="PDF modification tool with CLI and MCP interfaces" \
      org.opencontainers.image.source="https://github.com/mlorentedev/pdf-modifier-mcp" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="mlorentedev"
