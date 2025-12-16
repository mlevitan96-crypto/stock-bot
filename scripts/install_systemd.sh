#!/usr/bin/env bash
set -euo pipefail

# Installs/updates systemd service for this repo.
# Usage:
#   sudo ./scripts/install_systemd.sh /root/stock-bot trading-bot

REPO_DIR="${1:-/root/stock-bot}"
SERVICE_NAME="${2:-trading-bot}"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "[install_systemd] ERROR: run as root (use sudo)" >&2
  exit 1
fi

if [ ! -d "$REPO_DIR" ]; then
  echo "[install_systemd] ERROR: repo dir not found: $REPO_DIR" >&2
  exit 1
fi

if [ ! -f "$REPO_DIR/systemd_start.sh" ]; then
  echo "[install_systemd] ERROR: missing $REPO_DIR/systemd_start.sh" >&2
  exit 1
fi

chmod +x "$REPO_DIR/systemd_start.sh" || true

if [ ! -f "$REPO_DIR/.env" ]; then
  echo "[install_systemd] NOTE: $REPO_DIR/.env missing; creating from .env.example" >&2
  if [ -f "$REPO_DIR/.env.example" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
  else
    touch "$REPO_DIR/.env"
  fi
  chmod 600 "$REPO_DIR/.env" || true
fi

cat >"$UNIT_PATH" <<EOF
[Unit]
Description=Algorithmic Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${REPO_DIR}
EnvironmentFile=${REPO_DIR}/.env
ExecStart=${REPO_DIR}/systemd_start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "[install_systemd] OK: ${SERVICE_NAME} using ${REPO_DIR}"
