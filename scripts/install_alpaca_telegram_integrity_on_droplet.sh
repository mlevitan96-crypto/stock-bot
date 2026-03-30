#!/usr/bin/env bash
# Install Alpaca Telegram + integrity systemd units on the droplet (Alpaca only).
set -euo pipefail
REPO="${1:-/root/stock-bot}"
sudo cp "$REPO/deploy/systemd/alpaca-telegram-integrity.service" /etc/systemd/system/
sudo cp "$REPO/deploy/systemd/alpaca-telegram-integrity.timer" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alpaca-telegram-integrity.timer
sudo systemctl start alpaca-telegram-integrity.timer
echo "Installed alpaca-telegram-integrity.timer. Verify: systemctl list-timers | grep alpaca-telegram-integrity"
