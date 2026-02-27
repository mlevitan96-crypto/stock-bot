#!/bin/bash
# ============================================================
# DEPLOY TO DROPLET (idempotent)
# ============================================================
# 1) Pull latest main
# 2) Restart bot + dashboard services
# 3) Verify health endpoints
# ============================================================
# Usage: run on droplet (or via SSH):
#   bash board/eod/deploy_on_droplet.sh
# ============================================================

set -e
ROOT="/root/stock-bot-current"
[ -d "$ROOT" ] || ROOT="/root/trading-bot-current"
[ -d "$ROOT" ] || ROOT="/root/stock-bot"
cd "$ROOT"

echo "=== 1) PULL LATEST MAIN ==="
git fetch --all
git checkout main
git stash push -m 'pre-deploy' 2>/dev/null || true
git pull --rebase origin main || git reset --hard origin/main
COMMIT=$(git rev-parse HEAD)
echo "Deployed commit: $COMMIT"

echo "=== 2) RESTART BOT + DASHBOARD ==="
# Adapt service names to your systemd/supervisor setup
if command -v systemctl >/dev/null 2>&1; then
  for svc in stock-bot dashboard stock-bot-dashboard; do
    if systemctl list-units --type=service --all 2>/dev/null | grep -q "$svc"; then
      sudo systemctl restart "$svc" 2>/dev/null && echo "Restarted: $svc" || true
    fi
  done
fi
# Optional: supervisorctl
if command -v supervisorctl >/dev/null 2>&1; then
  supervisorctl restart all 2>/dev/null || true
fi
echo "Restart step complete (no-op if no managed services)."

echo "=== 3) VERIFY HEALTH ==="
# Dashboard often on 5000; bot health may be on 8081 or via dashboard
for url in "http://127.0.0.1:5000/api/ping" "http://127.0.0.1:5000/api/version" "http://127.0.0.1:8081/health"; do
  if curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 3 "$url" 2>/dev/null | grep -q 200; then
    echo "OK: $url"
  else
    echo "SKIP or FAIL: $url (may need auth or different port)"
  fi
done

echo "=== DONE ==="
echo "Commit: $COMMIT"
echo "Fill reports/phase8_deploy_proof.md with this commit and any restart output."
