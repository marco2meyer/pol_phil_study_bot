#!/usr/bin/env bash
set -euo pipefail

# Quick bootstrap for Ubuntu/Debian
if ! command -v docker >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Create project dir if not exists
mkdir -p /opt/pol_phil_study_bot

# Optional: enable UFW and allow only SSH, 8501, and Mongo 27017 (adjust as needed)
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 8501/tcp || true
  ufw allow 27017/tcp || true
fi

echo "Docker installed. Place project files under /opt/pol_phil_study_bot and create a .env with secrets."
