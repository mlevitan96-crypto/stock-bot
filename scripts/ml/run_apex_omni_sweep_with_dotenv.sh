#!/bin/bash
# Run apex omni sweep with Alpaca REST bars: sources repo .env (same as stock-bot.service EnvironmentFile).
set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/../../telemetry/alpaca_strict_completeness_gate.py" ]; then
  REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
  REPO="${APEX_SWEEP_REPO:-/root/stock-bot}"
fi
cd "$REPO"
set -a
# shellcheck source=/dev/null
[ -f .env ] && . ./.env
set +a
python3 -c "import os; print('ALPACA creds loaded:', bool(os.environ.get('ALPACA_API_KEY') or os.environ.get('ALPACA_KEY')))"
export PYTHONPATH="$REPO"
exec python3 "$REPO/scripts/ml/apex_omni_parameter_sweep.py" --root "$REPO" --fetch-bars-live
