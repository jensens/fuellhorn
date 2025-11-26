#!/bin/sh
# Fuellhorn - Lebensmittelvorrats-Verwaltung
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Docker entrypoint script
# Runs Alembic migrations and starts the application

set -e

echo "Running Alembic migrations..."
/app/.venv/bin/python -m alembic upgrade head

echo "Starting Fuellhorn application..."
exec /app/.venv/bin/python main.py
