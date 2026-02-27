#!/bin/bash
# ALPACA BARS — RESUME MODE (transient SSH recovery)
# No re-discovery. No re-mutation. Precondition: .env.research exists with ALPACA_KEY, ALPACA_SECRET, ALPACA_DATA_URL.
set -e
REPO=/root/stock-bot
cd "$REPO"
RESEARCH_ENV="$REPO/.env.research"
CRED_SOURCE=".env.research (derived from live trading)"

VERDICT_FILE="$REPO/reports/bars/final_verdict.txt"
_ensure_verdict_on_exit() {
  if [ -z "$_VERDICT_WRITTEN" ] && [ -n "$CRED_SOURCE" ]; then
    _range="(none)"
    [ -n "${START:-}" ] && [ -n "${END:-}" ] && _range="$START to $END"
    if [ -n "${_PHASE2_PASSED:-}" ]; then
      _req_out "$CRED_SOURCE" "${ALPACA_DATA_URL:-}" "PASS" "0" "$_range" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
    else
      _req_out "$CRED_SOURCE" "${ALPACA_DATA_URL:-}" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
    fi
  fi
}
_req_out() {
  _VERDICT_WRITTEN=1
  KEY_SOURCE="${1:-$CRED_SOURCE}"
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
}

trap _ensure_verdict_on_exit EXIT
_phase3_err_trap() {
  ec=$?; echo "[ERR] exit=$ec line=$LINENO cmd=$BASH_COMMAND pwd=$(pwd)" | tee -a "$REPO/reports/bars/fetch_debug.log" 2>/dev/null
  (ls -la "$REPO/scripts/" "$REPO/reports/bars/" 2>/dev/null) | tee -a "$REPO/reports/bars/fetch_debug.log" 2>/dev/null
  exit $ec
}
# ========== PRECONDITIONS ==========
if [ ! -f "$RESEARCH_ENV" ]; then
  _req_out "$CRED_SOURCE" "" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
set -a
source "$RESEARCH_ENV"
set +a
if [ -z "$ALPACA_KEY" ] || [ -z "$ALPACA_SECRET" ]; then
  _req_out "$CRED_SOURCE" "" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
if [ -z "$ALPACA_DATA_URL" ]; then
  _req_out "$CRED_SOURCE" "" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
export ALPACA_KEY ALPACA_SECRET ALPACA_DATA_URL

# ========== PHASE 2 — LIVE MARKET DATA VERIFICATION (same process as source above) ==========
echo "[Resume Phase 2] Verifying Market Data access (HTTP GET)..." 1>&2
RESP=$(curl -s -w "\nHTTP_CODE:%{http_code}\n" \
  -H "APCA-API-KEY-ID: $ALPACA_KEY" \
  -H "APCA-API-SECRET-KEY: $ALPACA_SECRET" \
  "$ALPACA_DATA_URL/v2/stocks/bars?symbols=SPY&timeframe=1Day&limit=5")
echo "$RESP"
echo "$RESP" | grep -qF '"bars"' || { _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"; exit 1; }
echo "$RESP" | grep -qF 'HTTP_CODE:200' || { _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "FAIL" "0" "(none)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"; exit 1; }
echo "[Resume Phase 2] PASS" 1>&2
_PHASE2_PASSED=1

# ========== PHASE 3 — FETCH HISTORICAL BARS ==========
echo "[Resume Phase 3] Fetching historical bars..." 1>&2
trap _phase3_err_trap ERR
mkdir -p "$REPO/reports/bars" "$REPO/data/bars"
FETCH_DEBUG="$REPO/reports/bars/fetch_debug.log"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) Phase 3A diagnostics pwd=$(pwd) ===" >> "$FETCH_DEBUG"
echo "--- data/bars ---" >> "$FETCH_DEBUG"
ls -lh "$REPO/data/bars/" >> "$FETCH_DEBUG" 2>&1
echo "--- dmesg tail (OOM/kill) ---" >> "$FETCH_DEBUG"
dmesg 2>/dev/null | tail -50 >> "$FETCH_DEBUG" 2>&1 || true
echo "--- Phase 3A done ---" >> "$FETCH_DEBUG"

set +e
trap - ERR
python3 -c "import pyarrow" 2>/dev/null || { pip3 install -q pyarrow 2>/dev/null || pip3 install --user -q pyarrow 2>/dev/null || pip3 install --break-system-packages -q pyarrow 2>/dev/null; true; }
trap _phase3_err_trap ERR
set -e
if ! python3 -c "import pyarrow" 2>/dev/null; then
  echo "pyarrow not available after install attempt; parquet write will fail" >> "$FETCH_DEBUG"
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "(pyarrow missing)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
python3 "$REPO/scripts/bars_universe_and_range.py" 2>/dev/null || true
START=""
END=""
SYMS=""
set +e
if [ -f "$REPO/reports/bars/universe_and_range.md" ]; then
  START=$(grep -E 'Start.*trading' "$REPO/reports/bars/universe_and_range.md" | head -1 | sed 's/.*|[[:space:]]*//;s/[[:space:]]*|.*//;s/^[[:space:]]*//;s/[[:space:]]*$//' || true)
  END=$(grep -E 'End.*max' "$REPO/reports/bars/universe_and_range.md" | head -1 | sed 's/.*|[[:space:]]*//;s/[[:space:]]*|.*//;s/^[[:space:]]*//;s/[[:space:]]*$//' || true)
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
" 2>/dev/null) || START="2024-01-01"
fi
[ -z "$END" ] && END=$(date -u +%Y-%m-%d 2>/dev/null) || true
[ -z "$END" ] && END=$(python3 -c "from datetime import datetime; print(datetime.utcnow().strftime('%Y-%m-%d'))" 2>/dev/null) || true
if [ -f "$REPO/reports/bars/universe_and_range.md" ]; then
  SYMS=$(sed -n '/^## Symbols/,/^$/p' "$REPO/reports/bars/universe_and_range.md" | tail -n +2 | tr -s ' \n' ',' | sed 's/,$//;s/,\.\.\.//;s/,,*/,/g' || true)
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
" 2>/dev/null) || true
fi
[ -z "$SYMS" ] && SYMS="SPY"
set -e
trap - ERR
if [ -z "$SYMS" ]; then
  echo "universe empty: bars_universe_and_range missing or unparsable" >> "$FETCH_DEBUG"
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "(universe empty)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
if [ -z "$START" ] || [ -z "$END" ]; then
  echo "range unparsable: START=$START END=$END" >> "$FETCH_DEBUG"
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "(range missing)" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi

echo "--- fetch run ---" >> "$FETCH_DEBUG"
set +e
python3 -u "$REPO/scripts/fetch_alpaca_bars.py" --symbols "$SYMS" --start "$START" --end "$END" --timeframe 1Day --out "$REPO/data/bars/alpaca_daily.parquet" --chunk-size 15 >> "$FETCH_DEBUG" 2>&1
FETCH_RC=$?
set -e
if [ $FETCH_RC -ne 0 ]; then
  echo "[Resume Phase 3] Fetch failed (rc=$FETCH_RC); tail of fetch_debug.log:" 1>&2
  tail -100 "$FETCH_DEBUG" 2>/dev/null || true
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "$START to $END" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi

# ========== PHASE 4 — INTEGRITY AUDIT ==========
echo "[Resume Phase 4] Running integrity audit..." 1>&2
set +e
python3 scripts/audit_bars.py --in "$REPO/data/bars/alpaca_daily.parquet"
AUDIT_RC=$?
set -e
if [ $AUDIT_RC -ne 0 ]; then
  _req_out "$CRED_SOURCE" "$ALPACA_DATA_URL" "PASS" "0" "$START to $END" "0/0/0" "NO" "BARS MISSING — FIX REQUIRED"
  exit 1
fi
python3 scripts/write_bars_cache_status.py --path "$REPO/data/bars/alpaca_daily.parquet" 2>/dev/null || true

# ========== PHASE 5 — REAL PNL REPLAY ==========
echo "[Resume Phase 5] Running blocked_expectancy and signal pipeline..." 1>&2
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
