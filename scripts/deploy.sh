#!/usr/bin/env bash
set -euo pipefail

# Deploy or redeploy on a GCE VM.
# Usage: ./scripts/deploy.sh [<gce-instance-name>] [<zone>]

INSTANCE="${1:-}"
ZONE="${2:-us-central1-a}"
PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -z "$INSTANCE" ]; then
  echo "Local deploy – pulling latest and restarting..."
  git pull --ff-only
  docker compose up -d --build
  exit 0
fi

echo "Deploying to $INSTANCE ($ZONE) in project $PROJECT..."

# Sync the repo (excluding secrets and volumes)
gcloud compute scp --recurse --zone="$ZONE" \
  --exclude='.env,credentials/,pb/pb_data/' \
  ./ "$INSTANCE":~/chatbot/

# Run setup on the remote VM
gcloud compute ssh "$INSTANCE" --zone="$ZONE" --command="
  cd ~/chatbot
  bash scripts/setup.sh
"

echo "Deployed. SSH into the VM and edit .env if needed."
