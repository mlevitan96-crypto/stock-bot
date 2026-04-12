#!/usr/bin/env bash
# One-shot "clean slate" on the Alpaca droplet: telemetry logs, bars caches, runtime state,
# feature store. Preserves state/kill_switch.json if present (do not accidentally re-enable
# trading after an intentional halt).
#
# Usage (from operator workstation):
#   ssh alpaca 'bash -s' < scripts/ops/droplet_clean_slate_purge.sh
# Or on-droplet:
#   bash /root/stock-bot/scripts/ops/droplet_clean_slate_purge.sh

set -euo pipefail
ROOT="${ALPACA_ROOT:-/root/stock-bot}"
cd "$ROOT" || { echo "error: cannot cd to $ROOT" >&2; exit 1; }

mkdir -p logs data/bars data/bars_cache state state/heartbeats feature_store

echo "=== PRE-PURGE (du -sm) ==="
for p in logs data/bars data/bars_cache state feature_store; do
  if [[ -e "$p" ]]; then du -sm "$p" 2>/dev/null || true; else echo "0 $p (missing)"; fi
done
[[ -f data/feature_store.jsonl ]] && du -sm data/feature_store.jsonl || true

PRE_JSONL_LOG=$(find logs -type f \( -name "*.jsonl" -o -name "*.log" -o -name "*.bak*" \) 2>/dev/null | wc -l) || true
PRE_STATE=$(find state -maxdepth 1 -type f \( -name "*.json" -o -name "*.jsonl" -o -name "*.flag" \) ! -name kill_switch.json 2>/dev/null | wc -l) || true
PRE_HB=$(find state/heartbeats -type f -name "*.json" 2>/dev/null | wc -l) || true
PRE_BARS=$(find data/bars -type f 2>/dev/null | wc -l) || true
PRE_BC=0
[[ -d data/bars_cache ]] && PRE_BC=$(find data/bars_cache -type f 2>/dev/null | wc -l) || true
PRE_FS=0
[[ -d feature_store ]] && PRE_FS=$(find feature_store -type f 2>/dev/null | wc -l) || true

PRE_BYTES=0
for _p in logs data/bars data/bars_cache state feature_store; do
  [[ -e "$_p" ]] || continue
  _b=$(du -sb "$_p" 2>/dev/null | cut -f1) || _b=0
  PRE_BYTES=$((PRE_BYTES + ${_b:-0}))
done

echo "PRE_COUNTS jsonl_and_log_files=$PRE_JSONL_LOG state_runtime_files=$PRE_STATE heartbeat_json=$PRE_HB bar_files=$PRE_BARS bars_cache_files=$PRE_BC feature_store_files=$PRE_FS"

echo "=== PURGING ==="
find logs -type f \( -name "*.jsonl" -o -name "*.log" -o -name "*.bak*" \) -delete

if [[ -d data/bars ]]; then find data/bars -mindepth 1 -maxdepth 1 -exec rm -rf {} +; fi
if [[ -d data/bars_cache ]]; then find data/bars_cache -mindepth 1 -maxdepth 1 -exec rm -rf {} +; fi

find state -maxdepth 1 -type f \( -name "*.json" -o -name "*.jsonl" -o -name "*.flag" \) ! -name kill_switch.json -delete
if [[ -d state/heartbeats ]]; then find state/heartbeats -type f -name "*.json" -delete; fi

if [[ -d feature_store ]]; then find feature_store -mindepth 1 -delete; fi
rm -f data/feature_store.jsonl

mkdir -p logs data/bars data/bars_cache state state/heartbeats feature_store

POST_BYTES=0
for _p in logs data/bars data/bars_cache state feature_store; do
  [[ -e "$_p" ]] || continue
  _b=$(du -sb "$_p" 2>/dev/null | cut -f1) || _b=0
  POST_BYTES=$((POST_BYTES + ${_b:-0}))
done
FREED=$((PRE_BYTES - POST_BYTES))

echo "=== POST-PURGE ==="
echo "PRE_BYTES_COMBINED=$PRE_BYTES POST_BYTES_COMBINED=$POST_BYTES approx_FREED_BYTES=$FREED"
du -sm logs data/bars data/bars_cache state feature_store 2>/dev/null || true
echo "logs listing (first 20):"
ls -la logs 2>/dev/null | head -n 20 || true

echo "=== RESTART stock-bot ==="
systemctl restart stock-bot
sleep 3
systemctl is-active stock-bot || true
systemctl status stock-bot --no-pager -l | head -n 28

echo "=== JOURNAL (last 30 lines) ==="
journalctl -u stock-bot -n 30 --no-pager || true

echo "=== DONE ==="
