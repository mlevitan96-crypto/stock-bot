#!/bin/bash
# Run Phase 5 effectiveness + Phase 6 baseline/recommend on an EXISTING backtest dir.
# Use this on the droplet after a backtest, or when you have a backtest dir with backtest_exits.jsonl.
#
# Usage: BACKTEST_DIR=backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS bash board/eod/run_profitability_on_backtest_dir.sh
#    or: bash board/eod/run_profitability_on_backtest_dir.sh backtests/30d_after_signal_engine_block3g_20260218_002100

set -e
ROOT="/root/stock-bot-current"
[ -d "$ROOT" ] || ROOT="/root/trading-bot-current"
[ -d "$ROOT" ] || ROOT="/root/stock-bot"
[ -d "$ROOT" ] || ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DIR="${BACKTEST_DIR:-$1}"
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  echo "Usage: BACKTEST_DIR=<path> $0   OR   $0 <backtest_dir>"
  echo "Example: $0 backtests/30d_after_signal_engine_block3g_20260218_002100"
  exit 1
fi

echo "=== Profitability pipeline on $DIR ==="
python3 scripts/analysis/run_effectiveness_reports.py --backtest-dir "$DIR" --out-dir "$DIR/effectiveness" || true
python3 scripts/governance/regression_guards.py || true
python3 scripts/governance/profitability_baseline_and_recommend.py --effectiveness-dir "$DIR/effectiveness" --out "$DIR" || true
python3 scripts/governance/generate_recommendation.py --backtest-dir "$DIR" || true
echo "=== Done. Check $DIR/effectiveness/ and $DIR/profitability_*.json $DIR/profitability_*.md $DIR/profitability_recommendation.md ==="
