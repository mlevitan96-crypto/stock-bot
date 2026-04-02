#!/usr/bin/env bash
# ============================================
# PAPER EXECUTION PROMO — SAFE RESTART
# ============================================
# Scope:
# - Paper trading ONLY
# - Enables PASSIVE_THEN_CROSS TTL=3 for top-20 universe
# - Starts non-blocking worker via systemd timer
# - No live order paths touched
#
# MUST run as root on the Alpaca droplet (e.g. ssh root@alpaca).
# ============================================

set -euo pipefail

cd /root/stock-bot

echo "=== Verifying git state ==="
git rev-parse HEAD

echo "=== Verifying paper universe exists ==="
ls -lh reports/daily/2026-04-01/evidence/EXEC_MODE_UNIVERSE_TOP20_LAST3D.json

echo "=== Installing paper exec promo environment ==="
mkdir -p /etc/systemd/system/stock-bot.service.d
cat << 'EOF' > /etc/systemd/system/stock-bot.service.d/paper-exec-promo.conf
[Service]
Environment=PAPER_EXEC_PROMO_ENABLED=1
Environment=PAPER_EXEC_TTL_MINUTES=3
Environment=PAPER_EXEC_UNIVERSE_PATH=/root/stock-bot/reports/daily/2026-04-01/evidence/EXEC_MODE_UNIVERSE_TOP20_LAST3D.json
Environment=PAPER_EXEC_FAIL_CLOSED=1
EOF

echo "=== Reloading systemd and restarting stock-bot ==="
systemctl daemon-reload
systemctl restart stock-bot

echo "=== Installing paper exec worker units ==="
cp deploy/systemd/paper-exec-mode-worker.service /etc/systemd/system/
cp deploy/systemd/paper-exec-mode-worker.timer /etc/systemd/system/

echo "=== Enabling and starting worker timer ==="
systemctl daemon-reload
systemctl enable --now paper-exec-mode-worker.timer

echo "=== Status check ==="
systemctl status stock-bot --no-pager || true
systemctl status paper-exec-mode-worker.timer --no-pager || true

echo "=== Tail recent logs ==="
journalctl -u stock-bot --since "5 minutes ago" --no-pager | tail -n 50
journalctl -u paper-exec-mode-worker --since "5 minutes ago" --no-pager | tail -n 50

echo "=== Restart complete. Paper exec promo is LIVE (paper-only). ==="
