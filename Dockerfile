# Fuellhorn - Lebensmittelvorrats-Verwaltung
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Production Dockerfile: Abhängigkeiten exakt aus uv.lock, Anwendung als veröffentlichtes Wheel von PyPI

FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

# Version als Build-Argument (wird vom Release-Workflow gesetzt; leer = neueste PyPI-Version)
ARG FUELLHORN_VERSION

WORKDIR /app

# SQLite-Datei und Daten liegen im Volume unter /app/data, nicht im Paket (#371)
ENV FUELLHORN_DATA_DIR=/app/data
# Virtuelle Umgebung mit den gelockten Abhängigkeiten zuerst im PATH
ENV PATH="/app/.venv/bin:$PATH"

# 1. Abhängigkeiten exakt wie in Tests und CI (uv.lock), ohne das Projekt selbst:
#    kein Build aus dem Repo nötig, keine frische Auflösung mit neueren Versionen (#414)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2. Die veröffentlichte Anwendung ohne erneute Dependency-Auflösung dazu
RUN uv pip install --python /app/.venv/bin/python --no-deps "fuellhorn${FUELLHORN_VERSION:+==$FUELLHORN_VERSION}"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

# Fuellhorn CLI führt Migrations aus und startet die App
CMD ["fuellhorn"]
