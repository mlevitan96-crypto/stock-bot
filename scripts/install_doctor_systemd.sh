#!/usr/bin/env bash
set -euo pipefail

# Installs a systemd timer that runs doctor.py periodically.
# Usage:
#   sudo ./scripts/install_doctor_systemd.sh /root/stock-bot trading-bot

REPO_DIR="${1:-/root/stock-bot}"
SERVICE_NAME="${2:-trading-bot}"

DOCTOR_SERVICE="trading-bot-doctor"
DOCTOR_UNIT="/etc/systemd/system/${DOCTOR_SERVICE}.service"
DOCTOR_TIMER="/etc/systemd/system/${DOCTOR_SERVICE}.timer"

if [ "$(id -u)" -ne 0 ]; then
  echo "[install_doctor] ERROR: run as root (use sudo)" >&2
  exit 1
fi

if [ ! -d "$REPO_DIR" ]; then
  echo "[install_doctor] ERROR: repo dir not found: $REPO_DIR" >&2
  exit 1
fi

if [ ! -f "$REPO_DIR/doctor.py" ]; then
  echo "[install_doctor] ERROR: missing $REPO_DIR/doctor.py" >&2
  exit 1
fi

cat >"$DOCTOR_UNIT" <<EOF
[Unit]
Description=Trading Bot Doctor (self-healing)
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=${REPO_DIR}
Environment=REPO_DIR=${REPO_DIR}
Environment=BOT_SERVICE_NAME=${SERVICE_NAME}
Environment=BOT_HEALTH_URL=http://127.0.0.1:8080/health
ExecStart=/usr/bin/python3 ${REPO_DIR}/doctor.py
EOF

cat >"$DOCTOR_TIMER" <<EOF
[Unit]
Description=Run Trading Bot Doctor periodically

[Timer]
OnBootSec=45
OnUnitActiveSec=60
AccuracySec=10
Unit=${DOCTOR_SERVICE}.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now "${DOCTOR_SERVICE}.timer"

echo "[install_doctor] OK: ${DOCTOR_SERVICE}.timer enabled"
