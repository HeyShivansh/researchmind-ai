# =============================================================================
# ResearchMind AI — Backend Dockerfile
# =============================================================================
# Multi-stage build:
#   1. builder  — Install Python dependencies with uv
#   2. production — Minimal runtime image
#
# Uses python:3.13-slim (Debian-based, glibc) instead of Alpine because
# PyMuPDF ships pre-compiled manylinux wheels that require glibc's
# libstdc++.so.6.  Alpine's musl libc is incompatible.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Install dependencies (cached independently of source code)
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Install uv (fast Python package installer) from a pinned version
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /bin/uv

WORKDIR /app

# Copy only dependency manifests first for better Docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# ---------------------------------------------------------------------------
# Stage 2 — Production image
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS production

# python:3.13-slim is Debian-based with glibc, so PyMuPDF's manylinux
# wheels work out of the box — no additional system libraries needed.

WORKDIR /app

# Copy the pre-built virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Ensure the virtualenv's python is used
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# Copy application code
COPY entrypoint.sh ./
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY pyproject.toml ./

# Create storage dir, set execute bit, then set ownership in one pass
RUN mkdir -p /app/storage/papers && \
    chmod +x entrypoint.sh && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Health check — uses the /health endpoint with Python's urllib
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run with entrypoint — runs migrations, then starts uvicorn
CMD ["./entrypoint.sh"]
