#!/usr/bin/env bash
# CURSOR_ALPACA_BARS_REMINDER_AND_CHECK.sh
# Reminder + verification block. No behavior changes.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="alpaca_bars_reminder_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/alpaca_bars_${RUN_TAG}"
LOG="/tmp/cursor_alpaca_bars_reminder.log"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== START ALPACA BARS REMINDER ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Authoritative reminder: Alpaca bars API
# -------------------------------------------------
cat > "${RUN_DIR}/ALPACA_BARS_REMINDER.md" <<'EOF'
# Alpaca Market Data (Bars) — Reminder

Bars are fetched from the **Market Data API**, NOT the trading API.

Base URL:
https://data.alpaca.markets

Stocks bars endpoint:
GET /v2/stocks/bars

Required headers:
- APCA-API-KEY-ID
- APCA-API-SECRET-KEY

Trading hosts (paper-api.alpaca.markets / api.alpaca.markets)
DO NOT serve bars.

Python SDK reference:
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

client = StockHistoricalDataClient(API_KEY, API_SECRET)
bars = client.get_stock_bars(
    StockBarsRequest(
        symbol_or_symbols=["AAPL"],
        timeframe=TimeFrame.Minute,
        start=start,
        end=end
    )
)
EOF

log "Wrote Alpaca bars reminder"

# -------------------------------------------------
# 2) Check for prior Alpaca bar-fetch implementations
# -------------------------------------------------
log "Scanning repo for prior Alpaca bar-fetch code"

grep -R "alpaca" -n src scripts 2>/dev/null | grep -Ei "bars|market|data|StockBars|data.alpaca" \
  > "${RUN_DIR}/prior_alpaca_bar_code.txt" || true

if [ -s "${RUN_DIR}/prior_alpaca_bar_code.txt" ]; then
  log "Found prior Alpaca bar-fetch references"
else
  log "No prior Alpaca bar-fetch references found"
fi

# -------------------------------------------------
# 3) Environment sanity check (keys presence)
# -------------------------------------------------
log "Checking Alpaca API keys in environment"

python3 - <<'PY' > "${RUN_DIR}/alpaca_env_check.json"
import os, json
print(json.dumps({
  "ALPACA_API_KEY_set": bool(os.getenv("ALPACA_API_KEY")),
  "ALPACA_API_SECRET_set": bool(os.getenv("ALPACA_API_SECRET"))
}, indent=2))
PY

# -------------------------------------------------
# 4) Summary for Cursor
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}

WHAT THIS BLOCK DID:
- Reminded Cursor that Alpaca bars come from https://data.alpaca.markets
- Documented correct endpoint, headers, and SDK usage
- Checked repo for prior Alpaca bar-fetch implementations
- Checked whether Alpaca API keys are present in the environment

NEXT (Cursor should do):
1) Reuse or align with any prior bar-fetch code found.
2) Ensure fetch_missing_bars_from_alpaca.py uses data.alpaca.markets.
3) Ensure ALPACA_API_KEY / ALPACA_API_SECRET are set on the droplet.
4) Re-run:
   python scripts/run_fetch_missing_bars_and_grid_on_droplet.py

GOAL:
- Populate data/bars for missing symbol-dates
- Re-run exit grid search with real bar coverage
- Produce a PROMOTE_TOP_CONFIG when evidence supports it

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: ALPACA_BARS_REMINDER_COMPLETE"

log "=== COMPLETE ALPACA BARS REMINDER ==="
