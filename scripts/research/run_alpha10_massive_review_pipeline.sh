#!/usr/bin/env bash
# Alpha 10 Massive Review — full offline lab (run after bell / truth warehouse settled).
# Droplet default root; override with TRADING_BOT_ROOT or STOCKBOT_ROOT.
set -euo pipefail
ROOT="${TRADING_BOT_ROOT:-${STOCKBOT_ROOT:-/root/stock-bot}}"
cd "$ROOT"
if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  set -a && . "$ROOT/.env" && set +a
elif [[ -f /root/.alpaca_env ]]; then
  # shellcheck disable=SC1091
  set -a && . /root/.alpaca_env && set +a
fi
export PYTHONPATH=.
PY="${ROOT}/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi
mkdir -p "$ROOT/reports/research"

# 1) Pull final closing / truth-warehouse + PnL audit (authoritative DATA_READY path)
"$PY" "$ROOT/scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py" \
  --root "$ROOT" --days 90 --max-compute

# 2) Label strict cohort (+1.3% / -0.65% first-touch) + merge ultra-dense features
"$PY" "$ROOT/scripts/research/prepare_training_data.py" \
  --root "$ROOT" \
  --out-jsonl "$ROOT/reports/research/alpha10_labeled_cohort.jsonl"

# 3) Combinatorial Alpha-10 review (clusters of 3–4 algorithm families)
"$PY" "$ROOT/scripts/research/massive_alpha_review.py" \
  --in-jsonl "$ROOT/reports/research/alpha10_labeled_cohort.jsonl" \
  --out-md "$ROOT/reports/research/ALPHA_10_MASSIVE_REVIEW.md"

echo "Alpha 10 pipeline complete -> $ROOT/reports/research/ALPHA_10_MASSIVE_REVIEW.md"
