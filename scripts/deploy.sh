#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/deploy.sh <server_ip> [bot_name]
# If bot_name is provided, only that bot is deployed and its env.server is copied to bots/<bot>/env on the server.

SERVER_IP=${1:-}
BOT_NAME=${2:-}
if [[ -z "$SERVER_IP" ]]; then
  echo "Usage: $0 <server_ip> [bot_name]" >&2
  exit 1
fi

REMOTE_DIR=/opt/pol_phil_study_bot

echo "==> Rsync project to $SERVER_IP:$REMOTE_DIR (excluding env files)"
rsync -az --delete \
  --exclude-from=.dockerignore \
  --exclude '.git/' \
  --exclude 'scripts/*.sh~' \
  ./ root@"$SERVER_IP":"$REMOTE_DIR"/

# Copy root .env for compose (Mongo credentials, etc.)
if [[ -f ./.env ]]; then
  echo "==> Copy ./.env to server:$REMOTE_DIR/.env"
  scp ./.env root@"$SERVER_IP":"$REMOTE_DIR/.env"
else
  echo "[WARN] ./.env not found locally; Mongo service may fail without required vars" >&2
fi

# Copy per-bot env if a bot is specified
if [[ -n "$BOT_NAME" ]]; then
  LOCAL_ENV_FILE="bots/${BOT_NAME}/.env.server"
  REMOTE_ENV_FILE="${REMOTE_DIR}/bots/${BOT_NAME}/env"
  if [[ ! -f "$LOCAL_ENV_FILE" ]]; then
    echo "Error: $LOCAL_ENV_FILE not found. Create it with production secrets for ${BOT_NAME}." >&2
    exit 2
  fi
  echo "==> Copy ${LOCAL_ENV_FILE} to server:${REMOTE_ENV_FILE}"
  scp "$LOCAL_ENV_FILE" root@"$SERVER_IP":"$REMOTE_ENV_FILE"
fi

echo "==> Build and start containers on server"
ssh root@"$SERVER_IP" bash -lc "\
  set -euo pipefail; \
  test -f '$REMOTE_DIR/docker-compose.yml' || { echo 'docker-compose.yml missing in $REMOTE_DIR' >&2; exit 3; }; \
  # Determine compose command
  if docker compose version >/dev/null 2>&1; then COMPOSE_CMD='docker compose'; \
  elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD='docker-compose'; \
  else echo 'Neither docker compose nor docker-compose found on server' >&2; exit 4; fi; \
  echo Using compose command: \"\$COMPOSE_CMD\"; \
  \$COMPOSE_CMD -f '$REMOTE_DIR/docker-compose.yml' config >/dev/null; \
  \$COMPOSE_CMD -f '$REMOTE_DIR/docker-compose.yml' build --pull \
"

if [[ -n "$BOT_NAME" ]]; then
  # Start only the requested bot (and dependencies via compose)
  echo "==> Starting service: ${BOT_NAME}"
  ssh root@"$SERVER_IP" bash -lc "\
    set -euo pipefail; \
    if docker compose version >/dev/null 2>&1; then COMPOSE_CMD='docker compose'; \
    elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD='docker-compose'; \
    else echo 'Neither docker compose nor docker-compose found on server' >&2; exit 4; fi; \
    \$COMPOSE_CMD -f '$REMOTE_DIR/docker-compose.yml' up -d ${BOT_NAME} \
  "
else
  # Start all
  ssh root@"$SERVER_IP" bash -lc "\
    set -euo pipefail; \
    if docker compose version >/dev/null 2>&1; then COMPOSE_CMD='docker compose'; \
    elif command -v docker-compose >/dev/null 2>&1; then COMPOSE_CMD='docker-compose'; \
    else echo 'Neither docker compose nor docker-compose found on server' >&2; exit 4; fi; \
    \$COMPOSE_CMD -f '$REMOTE_DIR/docker-compose.yml' up -d \
  "
fi

echo "Deployment finished. Server: $SERVER_IP"
