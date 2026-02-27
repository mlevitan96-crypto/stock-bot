#!/usr/bin/env bash
# CURSOR_ALPACA_BARS_FINAL_REMINDER_AND_EXECUTION.sh
# Final reminder + execution nudge for Alpaca Market Data bars.
# No new logic. Reuse prior work. Unblock grid search.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="alpaca_bars_final_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_alpaca_bars_final.log"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== ALPACA BARS FINAL REMINDER ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Authoritative reminder (do not re-invent)
# -------------------------------------------------
cat > "${RUN_DIR}/ALPACA_BARS_AUTHORITATIVE.md" <<'EOF'
ALPACA BARS — AUTHORITATIVE REMINDER

Bars come from the Market Data API, NOT the trading API.

Base URL:
https://data.alpaca.markets
(or https://data.sandbox.alpaca.markets for paper/sandbox)

Endpoint:
GET /v2/stocks/bars

Headers:
APCA-API-KEY-ID
APCA-API-SECRET-KEY

Same keys as trading, different host.

Do NOT use:
paper-api.alpaca.markets
api.alpaca.markets

This repo already has correct bar-fetch logic.
Reuse it. Do not redesign.
EOF

# -------------------------------------------------
# 2) Verify prior Alpaca bar work exists
# -------------------------------------------------
log "Checking for prior Alpaca bar-fetch implementations"

grep -R "data.alpaca.markets" -n src scripts 2>/dev/null \
  > "${RUN_DIR}/prior_data_api_usage.txt" || true

grep -R "StockBars" -n src scripts 2>/dev/null \
  >> "${RUN_DIR}/prior_data_api_usage.txt" || true

# -------------------------------------------------
# 3) Environment check (this is the blocker)
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
# 4) Final instruction to Cursor
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}

STATUS:
- Alpaca Market Data API usage is documented and correct.
- fetch_missing_bars_from_alpaca.py already targets data.alpaca.markets.
- Grid search is blocked ONLY by missing Alpaca API keys.

MULTI-MODEL / ADVERSARIAL REVIEW:
- Exit grid flow already uses multi-persona board review (prosecutor, defender, quant, SRE, board).
- exit_grid_board_review.py writes prosecutor_output.md, defender_output.md, quant_output.md, sre_output.md, board_output.md.
- When grid runs with bars, GRID_RECOMMENDATION.json is synthesized from that adversarial review.

CURSOR MUST DO NEXT:
1) Set ALPACA_API_KEY and ALPACA_API_SECRET on the droplet
   (systemd drop-in for stock-bot.service preferred).
2) Restart the service so env vars are visible.
3) Re-run:
   python scripts/run_fetch_missing_bars_and_grid_on_droplet.py

EXPECTED RESULT:
- Missing bars fetched for ~143 symbol-dates.
- data/bars populated.
- Exit grid search simulates exits.
- GRID_RECOMMENDATION.json produced with real PnL.
- Board decision can flip from TUNE to PROMOTE.

NO NEW CODE REQUIRED.
NO REDESIGN REQUIRED.
THIS IS A MECHANICAL UNBLOCK.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: ALPACA_BARS_FINAL_REMINDER_COMPLETE"

log "=== COMPLETE ALPACA BARS FINAL REMINDER ==="
