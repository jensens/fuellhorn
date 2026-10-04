#!/bin/bash
# Dev-Server für parallele Entwicklung
# Port = 8000 + Issue-Nummer (z.B. Issue 123 → Port 8123)
#
# Usage: ./scripts/dev-server.sh
#        ./scripts/dev-server.sh --no-seed  (ohne Testdaten)

set -e

# Issue-Nummer aus Worktree-Pfad extrahieren
CURRENT_DIR=$(pwd)
ISSUE_NUM=""

if [[ "$CURRENT_DIR" =~ \.worktrees/fuellhorn-([0-9]+) ]]; then
    ISSUE_NUM="${BASH_REMATCH[1]}"
    PORT=$((8000 + ISSUE_NUM))
    echo "📂 Worktree für Issue #$ISSUE_NUM erkannt"
else
    PORT=8080
    echo "📂 Hauptrepo (kein Worktree)"
fi

echo "🔌 Port: $PORT"

# Migrations ausführen
echo "🗄️  Migrations anwenden..."
uv run alembic upgrade head

# Testdaten laden (außer --no-seed)
if [[ "$1" != "--no-seed" ]]; then
    echo "🌱 Testdaten initialisieren..."
    uv run python scripts/seed_testdata.py
fi

# Server starten
echo ""
echo "🚀 Server starten auf http://localhost:$PORT"
echo "   Login: admin / admin123"
echo ""
echo "   Strg+C zum Beenden"
echo ""

PORT=$PORT uv run python main.py
