#!/bin/bash
# ============================================================
# RUN PROFITABILITY COMPARISON ON DROPLET (Phase 6)
# ============================================================
# Compares baseline vs proposed backtest dirs; runs regression guards.
# Writes reports/governance_comparison/comparison.json and comparison.md
#
# Usage (on droplet):
#   bash board/eod/run_profitability_compare_on_droplet.sh
#   bash board/eod/run_profitability_compare_on_droplet.sh --baseline backtests/30d_xxx --proposed backtests/30d_yyy
# ============================================================

set -e
ROOT="/root/stock-bot-current"
[ -d "$ROOT" ] || ROOT="/root/trading-bot-current"
[ -d "$ROOT" ] || ROOT="/root/stock-bot"
cd "$ROOT"

BASELINE=""
PROPOSED=""
while [ $# -gt 0 ]; do
  case "$1" in
    --baseline) BASELINE="$2"; shift 2 ;;
    --proposed) PROPOSED="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$BASELINE" ] || [ -z "$PROPOSED" ]; then
  # Use two most recent backtest dirs (with backtest_exits.jsonl) as baseline and proposed
  for d in $(ls -td backtests/30d_* 2>/dev/null | head -5); do
    [ -f "$d/backtest_exits.jsonl" ] || continue
    if [ -z "$PROPOSED" ]; then
      PROPOSED="$d"
    elif [ -z "$BASELINE" ]; then
      BASELINE="$d"
      break
    fi
  done
fi

if [ -z "$BASELINE" ] || [ -z "$PROPOSED" ]; then
  echo "Usage: $0 --baseline <backtest_dir> --proposed <backtest_dir>"
  echo "Or run from repo with at least two backtest dirs containing backtest_exits.jsonl"
  exit 1
fi

echo "=== PROFITABILITY COMPARISON ==="
echo "Baseline: $BASELINE"
echo "Proposed: $PROPOSED"

COMPARE_OUT="reports/governance_comparison"
mkdir -p "$COMPARE_OUT"
python3 scripts/governance/compare_backtest_runs.py --baseline "$BASELINE" --proposed "$PROPOSED" --out "$COMPARE_OUT" || true
python3 scripts/governance/regression_guards.py || true

echo "Comparison written to $COMPARE_OUT/comparison.json and comparison.md"
echo "=== DONE ==="
