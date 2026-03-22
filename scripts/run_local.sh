#!/usr/bin/env bash
set -euo pipefail

# ── Local development runner ────────────────────────────────
# Option 1: Docker (recommended)
# Option 2: Bare-metal (Python + PocketBase binary)

MODE="${1:-docker}"

case "$MODE" in
  docker)
    echo "Starting with Docker Compose (local override)..."
    if [ ! -f .env ]; then
      cp .env.local.example .env
      echo "Created .env from .env.local.example — edit it first."
      exit 1
    fi
    docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
    ;;

  bare)
    echo "Starting bare-metal (no Docker)..."
    if [ ! -f .env ]; then
      cp .env.local.example .env
      echo "Created .env from .env.local.example — edit it first."
      exit 1
    fi

    # Start PocketBase in background if not already running
    if ! curl -sf http://localhost:8090/api/health > /dev/null 2>&1; then
      if command -v pocketbase &>/dev/null; then
        echo "Starting PocketBase..."
        pocketbase serve --http=0.0.0.0:8090 --dir=./pb/pb_data --migrationsDir=./pb/pb_migrations &
        PB_PID=$!
        trap "kill $PB_PID 2>/dev/null" EXIT
        sleep 2
      else
        echo "ERROR: pocketbase binary not found. Install it or use 'docker' mode."
        exit 1
      fi
    else
      echo "PocketBase already running on :8090"
    fi

    # Start FastAPI with hot-reload
    echo "Starting FastAPI on :8000..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ;;

  *)
    echo "Usage: $0 [docker|bare]"
    exit 1
    ;;
esac
