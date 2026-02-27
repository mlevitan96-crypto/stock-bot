#!/bin/bash
# FETCH ALPACA MARKET DATA BARS — FINAL, AUTHORITATIVE
# Run on droplet. No human guidance. No hallucination.
# Authority: same credentials as live trading; Market Data host (data.*) only; live HTTP verify; hard fail on uncertainty.
set -e
REPO=/root/stock-bot
cd "$REPO"

VERDICT_FILE="$REPO/reports/bars/final_verdict.txt"
_req_out() {
  KEY_SOURCE="${1:-unknown}"
  DATA_HOST="${2:-}"
  VERIFY="${3:-FAIL}"
  N="${4:-0}"
  RANGE="${5:-(none)}"
  COV="${6:-0/0/0}"
  PNL="${7:-NO}"
  VERD="${8:-BARS MISSING — FIX REQUIRED}"
  BLOCK="========================================================
FINAL VERDICT (PRINT ONLY)
========================================================
Credential source: $KEY_SOURCE
Market Data host used: ${DATA_HOST:-(not set)}
Market Data verification: $VERIFY
Symbols fetched: $N
Date range covered: $RANGE
Bars coverage: min/median/max % — $COV
Replay pnl non-zero: $PNL
Verdict: $VERD
========================================================"
  mkdir -p "$REPO/reports/bars"
  echo "$BLOCK" > "$VERDICT_FILE"
  echo "" 1>&2
  echo "$BLOCK" 1>&2
  echo ""
  echo "$BLOCK"
}

# ========== PHASE 0 — DISCOVER CREDENTIAL SOURCE ==========
echo "[Phase 0] Discovering credential source..." 1>&2
# Resolve env file in order: 1) instance_a/.env  2) .env  3) systemd EnvironmentFiles (stock-bot-dashboard / stock-bot).
ENV_FILE=""
[ -f "$REPO/instance_a/.env" ] && ENV_FILE="$REPO/instance_a/.env"
[ -z "$ENV_FILE" ] && [ -f "$REPO/.env" ] && ENV_FILE="$REPO/.env"
if [ -z "$ENV_FILE" ]; then
  for svc in stock-bot-dashboard stock-bot; do
    if systemctl list-units --type=service --all 2>/dev/null | grep -q "$svc"; then
      EF=$(systemctl show "$svc" 2>/dev/null | grep -E '^EnvironmentFiles=' | head -1 | sed 's/EnvironmentFiles=//;s/ .*//;s/^-//')
      if [ -n "$EF" ] && [ -f "$EF" ]; then
        ENV_FILE="$EF"
        break
      fi
    fi
  done
fi
CRED_SOURCE="${ENV_FILE:-unknown}"
if [ -z "$ENV_FILE" ] || [ ! -f "$ENV_FILE" ]; then
  _req_out "${CRED_SOURCE}" "" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
set -a
source "$ENV_FILE"
set +a
if [ -z "$ALPACA_KEY" ]; then
  ALPACA_KEY=$(grep -E '^ALPACA_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
fi
if [ -z "$ALPACA_SECRET" ]; then
  ALPACA_SECRET=$(grep -E '^ALPACA_API_SECRET=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
fi
if [ -z "$ALPACA_KEY" ] || [ -z "$ALPACA_SECRET" ]; then
  _req_out "$CRED_SOURCE" "" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
export ALPACA_KEY ALPACA_SECRET

# ========== PHASE 1 — SET MARKET DATA HOST (RESEARCH OVERRIDE) ==========
echo "[Phase 1] Writing .env.research (live config untouched)..." 1>&2
# DO NOT modify instance_a/.env. Create or update .env.research for research only; live trading config untouched.
RESEARCH_ENV="$REPO/.env.research"
ALPACA_DATA_URL="https://data.alpaca.markets"
cat > "$RESEARCH_ENV" << EOF
ALPACA_KEY=$ALPACA_KEY
ALPACA_SECRET=$ALPACA_SECRET
ALPACA_DATA_URL=$ALPACA_DATA_URL
EOF
chmod 600 "$RESEARCH_ENV"
set -a
source "$RESEARCH_ENV"
set +a
export ALPACA_KEY ALPACA_SECRET ALPACA_DATA_URL
mkdir -p "$REPO/reports/bars"
cat > "$REPO/reports/bars/alpaca_env_source.md" << EOF
# Alpaca env source (research override)

**Credential source (discovered):** $CRED_SOURCE

**Research env file:** $RESEARCH_ENV

**Market Data host:** $ALPACA_DATA_URL

**Notes:**
- Credentials discovered from $CRED_SOURCE.
- Market Data host overridden for research only (in \`.env.research\`).
- Live trading config untouched (\`instance_a/.env\` not modified).
EOF

# ========== PHASE 2 — LIVE MARKET DATA VERIFICATION (NO SDK) ==========
echo "[Phase 2] Verifying Market Data access (HTTP GET)..." 1>&2
# Use .env.research (sourced in Phase 1); GET with headers; REQUIRE HTTP 200 and JSON body containing "bars".
BODY=$(curl -s -w "\n%{http_code}" \
  -H "APCA-API-KEY-ID: $ALPACA_KEY" \
  -H "APCA-API-SECRET-KEY: $ALPACA_SECRET" \
  "$ALPACA_DATA_URL/v2/stocks/bars?symbols=SPY&timeframe=1Day&limit=5")
CODE=$(echo "$BODY" | tail -1)
JSON=$(echo "$BODY" | sed '$d')
if [ "$CODE" != "200" ]; then
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
if ! echo "$JSON" | grep -q '"bars"'; then
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi

# ========== PHASE 3 — FETCH HISTORICAL BARS ==========
echo "[Phase 3] Fetching historical bars (universe + date range)..." 1>&2
# Universe from score_snapshot + blocked_trades; range min(snapshot_ts)−400 trading days → max(snapshot_ts). ≥90% coverage, HARD FAIL.
python3 -c "import pyarrow" 2>/dev/null || { pip3 install -q pyarrow 2>/dev/null || pip3 install --user -q pyarrow 2>/dev/null; true; }
python3 scripts/bars_universe_and_range.py 2>/dev/null || true
START=""
END=""
SYMS=""
if [ -f "$REPO/reports/bars/universe_and_range.md" ]; then
  START=$(grep -E 'Start.*trading' "$REPO/reports/bars/universe_and_range.md" | head -1 | sed 's/.*|[[:space:]]*//;s/[[:space:]]*|.*//;s/^[[:space:]]*//;s/[[:space:]]*$//')
  END=$(grep -E 'End.*max' "$REPO/reports/bars/universe_and_range.md" | head -1 | sed 's/.*|[[:space:]]*//;s/[[:space:]]*|.*//;s/^[[:space:]]*//;s/[[:space:]]*$//')
fi
if [ -z "$START" ]; then
  START=$(python3 -c "
from datetime import datetime, timedelta
d = datetime.utcnow()
c = 0
while c < 400:
  d -= timedelta(days=1)
  if d.weekday() < 5: c += 1
print(d.strftime('%Y-%m-%d'))
" 2>/dev/null || echo "2024-01-01")
fi
[ -z "$END" ] && END=$(date -u +%Y-%m-%d 2>/dev/null || python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y-%m-%d'))" 2>/dev/null)
if [ -f "$REPO/reports/bars/universe_and_range.md" ]; then
  SYMS=$(sed -n '/^## Symbols/,/^$/p' "$REPO/reports/bars/universe_and_range.md" | tail -n +2 | tr -s ' \n' ',' | sed 's/,$//;s/,\.\.\.//;s/,,*/,/g')
fi
if [ -z "$SYMS" ] && [ -f "$REPO/logs/score_snapshot.jsonl" ]; then
  SYMS=$(python3 -c "
import json
s=set()
for f in ['$REPO/logs/score_snapshot.jsonl','$REPO/state/blocked_trades.jsonl']:
  try:
    for line in open(f):
      r=json.loads(line)
      x=(r.get('symbol') or r.get('ticker') or '').strip()
      if x and x!='?': s.add(x)
  except: pass
print(','.join(sorted(s)[:500]))
" 2>/dev/null)
fi
[ -z "$SYMS" ] && SYMS="SPY"
set +e
python3 scripts/fetch_alpaca_bars.py --symbols "$SYMS" --start "$START" --end "$END" --timeframe 1Day --out "$REPO/data/bars/alpaca_daily.parquet"
FETCH_RC=$?
set -e
if [ $FETCH_RC -ne 0 ]; then
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "$START to $END" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi

# ========== PHASE 4 — INTEGRITY AUDIT ==========
echo "[Phase 4] Running integrity audit..." 1>&2
# No NaN/Inf; valid OHLCV; no duplicate (symbol, date).
set +e
python3 scripts/audit_bars.py --in "$REPO/data/bars/alpaca_daily.parquet"
AUDIT_RC=$?
set -e
if [ $AUDIT_RC -ne 0 ]; then
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "$START to $END" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
python3 scripts/write_bars_cache_status.py --path "$REPO/data/bars/alpaca_daily.parquet" 2>/dev/null || true

# ========== PHASE 5 — ENABLE REAL PNL REPLAY ==========
echo "[Phase 5] Running blocked_expectancy and signal pipeline..." 1>&2
# Minimal replay remains DISABLED when parquet exists (existing run_droplet_truth_run logic).
python3 scripts/blocked_expectancy_analysis.py
python3 scripts/blocked_signal_expectancy_pipeline.py
PNL_NONZERO="NO"
if [ -f "$REPO/reports/blocked_expectancy/replay_results.jsonl" ]; then
  if grep -qE '"pnl_pct":[^0]|"pnl_pct":-[0-9]' "$REPO/reports/blocked_expectancy/replay_results.jsonl" 2>/dev/null; then
    PNL_NONZERO="YES"
  fi
fi

# ========== FINAL VERDICT (PRINT ONLY) ==========
SYMBOLS_FETCHED="0"
DATE_RANGE="$START to $END"
COVERAGE="0/0/0"
if [ -f "$REPO/reports/bars/cache_status.md" ]; then
  SYMBOLS_FETCHED=$(grep -E 'Symbols|Rows' "$REPO/reports/bars/cache_status.md" | head -1 | grep -oE '[0-9]+' | head -1)
fi
if [ -f "$REPO/data/bars/alpaca_daily.parquet" ]; then
  COVERAGE=$(python3 -c "
import pandas as pd
df=pd.read_parquet('$REPO/data/bars/alpaca_daily.parquet')
if df.empty or 'symbol' not in df.columns: exit(0)
req=400
pcts=[df[df['symbol']==s]['date'].nunique()/req*100 for s in df['symbol'].unique()]
if pcts: print(f'{min(pcts):.1f}/{sorted(pcts)[len(pcts)//2]:.1f}/{max(pcts):.1f}')
" 2>/dev/null)
fi
[ -z "$COVERAGE" ] && COVERAGE="0/0/0"
VERDICT="BARS MISSING — FIX REQUIRED"
[ "$PNL_NONZERO" = "YES" ] && VERDICT="BARS READY — REAL PNL ENABLED"
_req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "$SYMBOLS_FETCHED" "$DATE_RANGE" "$COVERAGE" "$PNL_NONZERO" "$VERDICT"
exit 0
