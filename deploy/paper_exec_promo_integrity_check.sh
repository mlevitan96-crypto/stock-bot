#!/usr/bin/env bash
# =========================================================
# MID-SESSION INTEGRITY CHECK — PAPER EXEC PROMO
# =========================================================
# Safe, read-only, non-disruptive. No restarts, no config writes.
# Run on the droplet (root recommended for full journalctl access).
# =========================================================

set -euo pipefail

cd /root/stock-bot

echo "================================================="
echo "INTEGRITY CHECK — $(date -u)"
echo "================================================="

echo
echo "=== [1] Decision Flow Check ==="
if [ -f logs/paper_exec_mode_decisions.jsonl ]; then
  DECISIONS=$(wc -l < logs/paper_exec_mode_decisions.jsonl | tr -d ' ')
  echo "paper_exec_mode_decisions.jsonl lines: ${DECISIONS}"
  tail -n 3 logs/paper_exec_mode_decisions.jsonl || true
else
  echo "MISSING: logs/paper_exec_mode_decisions.jsonl"
fi

echo
echo "=== [2] Pending / Done Queue Health ==="
for f in state/paper_exec_pending.jsonl state/paper_exec_done.jsonl; do
  if [ -f "$f" ]; then
    echo "$(basename "$f"): $(wc -l < "$f" | tr -d ' ') lines"
  else
    echo "$(basename "$f"): MISSING"
  fi
done

echo
echo "=== [3] Worker Timer & Recent Activity ==="
systemctl status paper-exec-mode-worker.timer --no-pager || true
echo
journalctl -u paper-exec-mode-worker --since "90 minutes ago" --no-pager | tail -n 40 || true

echo
echo "=== [4] Paper-Only Safety Sanity ==="
echo "Searching for submit_order mentions in stock-bot logs (last 90 min):"
if out=$(journalctl -u stock-bot --since "90 minutes ago" --no-pager 2>/dev/null | grep -i submit_order | head -n 20); then
  echo "$out"
else
  echo "No submit_order entries found."
fi

echo
echo "=== [5] Market Data Freshness ==="
if [ -f artifacts/market_data/alpaca_bars.jsonl ]; then
  ls -lh artifacts/market_data/alpaca_bars.jsonl
  echo "Last 5 bars:"
  tail -n 5 artifacts/market_data/alpaca_bars.jsonl
else
  echo "MISSING: artifacts/market_data/alpaca_bars.jsonl"
fi

echo
echo "=== [6] Stock-Bot Service Health ==="
systemctl status stock-bot --no-pager || true
journalctl -u stock-bot --since "90 minutes ago" --no-pager | tail -n 40 || true

echo
echo "================================================="
echo "INTEGRITY CHECK COMPLETE"
echo "================================================="
