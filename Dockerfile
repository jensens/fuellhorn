# Fuellhorn - Lebensmittelvorrats-Verwaltung
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Simple Dockerfile for MVP - no multi-stage build, no security hardening yet
# Post-MVP improvements: Multi-stage build, non-root user, security hardening

FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies (creates .venv) - no dev dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY main.py ./

# Copy Alembic configuration and migrations
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DB_TYPE=sqlite
ENV DATABASE_URL=sqlite:///data/fuellhorn.db
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Expose port (NiceGUI default)
EXPOSE 8080

# Health check using the /api/health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

# Run the application via the venv Python
CMD ["/app/.venv/bin/python", "main.py"]
