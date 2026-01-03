# Fuellhorn - Lebensmittelvorrats-Verwaltung
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Production Dockerfile - installs from PyPI

FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

# Version als Build-Argument (wird vom Release-Workflow gesetzt)
ARG FUELLHORN_VERSION

WORKDIR /app

# Fuellhorn von PyPI installieren (inkl. Alembic-Migrations)
RUN uv pip install --system fuellhorn==${FUELLHORN_VERSION}

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

# Fuellhorn CLI führt Migrations aus und startet die App
CMD ["fuellhorn"]
