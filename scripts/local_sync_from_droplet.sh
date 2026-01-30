#!/bin/bash
# Pull EOD artifacts from droplet to local board/eod/out/.
# Set DROPLET_IP or we use droplet_config.json host. Run from repo root.
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
DROPLET_IP="${DROPLET_IP:-$(grep -o '"host"[[:space:]]*:[[:space:]]*"[^"]*"' droplet_config.json 2>/dev/null | sed -E 's/.*:[[:space:]]*"([^"]+)".*/\1/' || true)}"
if [ -z "$DROPLET_IP" ]; then
  echo "DROPLET_IP not set and could not read from droplet_config.json"
  exit 1
fi
mkdir -p board/eod/out
scp "root@${DROPLET_IP}:/root/stock-bot/board/eod/out/*.md" board/eod/out/
scp "root@${DROPLET_IP}:/root/stock-bot/board/eod/out/*.json" board/eod/out/
