#!/bin/bash
set -euo pipefail
ROOT="${ALPACA_ROOT:-/root/stock-bot}"
cd "$ROOT"
export PYTHONPATH="$ROOT"
TS="$(date -u +%Y%m%d_%H%M%SZ)"
mkdir -p reports/audit
exec "$ROOT/venv/bin/python" -u "$ROOT/scripts/audit/alpaca_forward_truth_contract_runner.py" \
  --root "$ROOT" \
  --window-hours 72 \
  --repair-max-rounds 6 \
  --repair-sleep-seconds 10 \
  --repair-internal-rounds-per-iteration 1 \
  --json-out "$ROOT/reports/ALPACA_FORWARD_TRUTH_RUN_${TS}.json" \
  --md-out "$ROOT/reports/audit/ALPACA_FORWARD_TRUTH_RUN_${TS}.md" \
  --incident-md "$ROOT/reports/audit/ALPACA_FORWARD_TRUTH_INCIDENT_${TS}.md" \
  --incident-json "$ROOT/reports/ALPACA_FORWARD_TRUTH_INCIDENT_${TS}.json"
