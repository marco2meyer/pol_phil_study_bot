#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/deploy.sh 91.99.128.203
SERVER_IP=${1:-}
if [[ -z "$SERVER_IP" ]]; then
  echo "Usage: $0 <server_ip>" >&2
  exit 1
fi

REMOTE_DIR=/opt/pol_phil_study_bot

# Sync project to server (excluding local-only files via .dockerignore + extras)
rsync -az --delete \
  --exclude-from=.dockerignore \
  --exclude '.git/' \
  --exclude 'scripts/*.sh~' \
  ./ root@"$SERVER_IP":"$REMOTE_DIR"/

# Ensure scripts are executable on server
ssh root@"$SERVER_IP" "chmod +x $REMOTE_DIR/scripts/*.sh || true"

# Build and start containers on server
ssh root@"$SERVER_IP" <<'EOF'
set -e
cd /opt/pol_phil_study_bot
# Ensure .env exists on server with secrets before this step
docker compose build --pull
docker compose up -d
EOF

echo "Deployed to $SERVER_IP. App should be on http://$SERVER_IP:8501"
