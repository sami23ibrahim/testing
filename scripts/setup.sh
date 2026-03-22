#!/usr/bin/env bash
set -euo pipefail

echo "=== RAG Chatbot – VM Setup ==="

# 1. Copy env template if .env doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example – edit it with your real values."
fi

# 2. Create credentials directory
mkdir -p credentials
echo "Place your GCP service-account JSON in ./credentials/service-account.json"

# 3. Install Docker + Compose if missing
if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  echo "Log out and back in for docker group to take effect."
fi

# 4. Start the stack
echo "Starting services..."
docker compose up -d --build

echo ""
echo "=== Done ==="
echo "  Caddy (proxy):    http://localhost"
echo "  FastAPI docs:     http://localhost/api/docs"
echo "  PocketBase admin: http://localhost/pb/_/"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your GCP project and credentials"
echo "  2. Open PocketBase admin and create the first admin account"
echo "  3. Create a rag_config with a system prompt and set is_active=true"
echo "  4. docker compose restart fastapi"
echo ""
echo "For local dev without Caddy:"
echo "  bash scripts/run_local.sh docker   # Docker with ports exposed"
echo "  bash scripts/run_local.sh bare     # Python + PocketBase directly"
