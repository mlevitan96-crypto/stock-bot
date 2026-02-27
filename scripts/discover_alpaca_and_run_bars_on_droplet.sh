#!/bin/bash
# DISCOVER ALPACA CREDENTIALS + ENABLE REAL BARS (RUN ON DROPLET)
# No guessing. No hardcoding. Hard fails.
set -e
REPO=/root/stock-bot
cd "$REPO"

# ========== PHASE 0 — LOCATE LIVE ALPACA CREDENTIALS ==========
SERVICE_NAME=""
ENV_FILE=""
for u in stock-bot-dashboard stock-bot uw-flow-daemon; do
  if systemctl list-units --type=service --all 2>/dev/null | grep -q "$u"; then
    SERVICE_NAME="$u"
    ENV_FILE=$(systemctl show "$SERVICE_NAME" 2>/dev/null | grep -E '^EnvironmentFiles=' | head -1 | sed 's/EnvironmentFiles=//' | tr ' ' '\n' | grep -E '\.env' | head -1)
    [ -n "$ENV_FILE" ] && break
    # Fallback: service uses WorkingDirectory + .env
    ENV_FILE="/root/stock-bot/.env"
    break
  fi
done
if [ -z "$SERVICE_NAME" ]; then
  SERVICE_NAME=$(systemctl list-units --type=service 2>/dev/null | grep -oE 'stock[^ ]*|bot[^ ]*' | head -1)
fi
if [ -z "$ENV_FILE" ]; then
  ENV_FILE="/root/stock-bot/.env"
fi
if [ ! -f "$ENV_FILE" ]; then
  echo "ALPACA KEYS NOT FOUND IN SERVICE ENV"
  echo "Env file missing: $ENV_FILE"
  echo ""
  echo "========================================================
REQUIRED OUTPUT
========================================================
Alpaca credential source: ${SERVICE_NAME:-unknown}
Alpaca API verification: FAIL
Symbols fetched: 0
Date range covered: (none)
Bars coverage: min/median/max % — 0/0/0
Replay pnl non-zero: NO
Verdict: BARS MISSING — FIX REQUIRED
========================================================"
  exit 1
fi
# Extract ALPACA_* (no export yet)
ALPACA_API_KEY=$(grep -E '^ALPACA_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
ALPACA_SECRET_KEY=$(grep -E '^ALPACA_SECRET_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
ALPACA_BASE_URL=$(grep -E '^ALPACA_BASE_URL=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
if [ -z "$ALPACA_API_KEY" ]; then
  ALPACA_API_KEY=$(grep -E '^ALPACA_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
fi
if [ -z "$ALPACA_SECRET_KEY" ]; then
  ALPACA_SECRET_KEY=$(grep -E '^ALPACA_API_SECRET=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
fi
if [ -z "$ALPACA_SECRET_KEY" ]; then
  ALPACA_SECRET_KEY=$(grep -E '^ALPACA_SECRET=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
fi
if [ -z "$ALPACA_API_KEY" ] || [ -z "$ALPACA_SECRET_KEY" ]; then
  echo "ALPACA KEYS NOT FOUND IN SERVICE ENV"
  echo "Service: $SERVICE_NAME EnvFile: $ENV_FILE"
  echo ""
  echo "========================================================
REQUIRED OUTPUT
========================================================
Alpaca credential source: ${SERVICE_NAME:-unknown}
Alpaca API verification: FAIL
Symbols fetched: 0
Date range covered: (none)
Bars coverage: min/median/max % — 0/0/0
Replay pnl non-zero: NO
Verdict: BARS MISSING — FIX REQUIRED
========================================================"
  exit 1
fi
[ -z "$ALPACA_BASE_URL" ] && ALPACA_BASE_URL="https://paper-api.alpaca.markets"

# ========== PHASE 1 — EXPORT RESEARCH ENV ==========
RESEARCH_ENV="$REPO/.env.research"
cat > "$RESEARCH_ENV" << EOF
ALPACA_API_KEY=$ALPACA_API_KEY
ALPACA_SECRET_KEY=$ALPACA_SECRET_KEY
ALPACA_BASE_URL=$ALPACA_BASE_URL
EOF
chmod 600 "$RESEARCH_ENV"
mkdir -p "$REPO/reports/bars"
cat > "$REPO/reports/bars/alpaca_env_source.md" << EOF
# Alpaca env source

**Service:** $SERVICE_NAME
**Env file used by service:** $ENV_FILE
**Research env:** $RESEARCH_ENV

Keys were sourced from the same env file used by the live service. No duplication of secrets; research env contains only ALPACA_* for bars pipeline.
EOF

# ========== PHASE 2 — VERIFY ALPACA ACCESS ==========
set -a
source "$RESEARCH_ENV"
set +a
python3 << 'PYEOF'
import os, sys
try:
    import requests
except ImportError:
    sys.exit(127)
base = os.environ.get("ALPACA_BASE_URL", "")
if "paper" in base.lower() or "sandbox" in base.lower():
    url = "https://data.sandbox.alpaca.markets"
else:
    url = "https://data.alpaca.markets"
r = requests.get(
    f"{url}/v2/stocks/bars",
    headers={
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    },
    params={"symbols": "SPY", "timeframe": "1Day", "limit": 5},
    timeout=15,
)
print("STATUS:", r.status_code)
print("BODY:", (r.text or "")[:300])
if r.status_code != 200:
    print("ALPACA DATA ACCESS FAILED")
    sys.exit(1)
sys.exit(0)
PYEOF
PYC=$?
if [ $PYC -ne 0 ]; then
  echo "ALPACA DATA ACCESS FAILED"
  echo ""
  echo "========================================================
REQUIRED OUTPUT
========================================================
Alpaca credential source: $SERVICE_NAME
Alpaca API verification: FAIL
Symbols fetched: 0
Date range covered: (none)
Bars coverage: min/median/max % — 0/0/0
Replay pnl non-zero: NO
Verdict: BARS MISSING — FIX REQUIRED
========================================================"
  exit 1
fi

# ========== PHASE 3 — RUN BARS PIPELINE ==========
set -a
source "$RESEARCH_ENV"
set +a
# Subprocess inherits ALPACA_*; check_alpaca_env does not override existing env.
python3 scripts/run_bars_pipeline.py
PIPERC=$?

# ========== PHASE 4 — FINAL PROOF ==========
PARQUET="$REPO/data/bars/alpaca_daily.parquet"
PROOF="$REPO/reports/bars/PROOF.md"
if [ $PIPERC -eq 0 ]; then
  if [ ! -f "$PARQUET" ] || [ ! -s "$PARQUET" ]; then
    echo "FAIL: $PARQUET missing or empty"
    exit 1
  fi
  if [ ! -f "$PROOF" ] || [ ! -s "$PROOF" ]; then
    echo "FAIL: $PROOF missing or empty"
    exit 1
  fi
fi

# ========== REQUIRED OUTPUT (ONE BLOCK) ==========
SYMBOLS_FETCHED=$(grep -E '^## Symbol count|Symbols fetched' "$PROOF" 2>/dev/null | tail -1 | grep -oE '[0-9]+' | head -1)
[ -z "$SYMBOLS_FETCHED" ] && SYMBOLS_FETCHED="0"
DATE_RANGE=$(grep -E '^## Date range|Date range covered' "$PROOF" 2>/dev/null | tail -1 | sed 's/^## Date range//;s/^Date range covered//;s/^[[:space:]]*//;s/[[:space:]]*$//')
[ -z "$DATE_RANGE" ] && DATE_RANGE="(none)"
COV_LINE=$(grep -E 'min/median/max|Bars coverage' "$PROOF" 2>/dev/null | tail -1)
COVERAGE=$(echo "$COV_LINE" | grep -oE '[0-9.]+/[0-9.]+/[0-9.]+' | head -1)
[ -z "$COVERAGE" ] && COVERAGE="0/0/0"
PNL_NONZERO="NO"
if [ -f "$REPO/reports/blocked_expectancy/replay_results.jsonl" ]; then
  if grep -q '"pnl_pct":[^0]' "$REPO/reports/blocked_expectancy/replay_results.jsonl" 2>/dev/null || grep -q '"pnl_pct": -' "$REPO/reports/blocked_expectancy/replay_results.jsonl" 2>/dev/null; then
    PNL_NONZERO="YES"
  fi
fi
if [ $PIPERC -eq 0 ] && [ "$PNL_NONZERO" = "YES" ]; then
  VERDICT="BARS READY — REAL PNL ENABLED"
else
  VERDICT="BARS MISSING — FIX REQUIRED"
fi
echo ""
echo "========================================================
REQUIRED OUTPUT
========================================================
Alpaca credential source: $SERVICE_NAME
Alpaca API verification: PASS
Symbols fetched: $SYMBOLS_FETCHED
Date range covered: $DATE_RANGE
Bars coverage: min/median/max % — $COVERAGE
Replay pnl non-zero: $PNL_NONZERO
Verdict: $VERDICT
========================================================"
exit $PIPERC
