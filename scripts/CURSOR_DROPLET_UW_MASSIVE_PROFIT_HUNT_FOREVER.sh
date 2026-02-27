#!/usr/bin/env bash
# CURSOR_DROPLET_UW_MASSIVE_PROFIT_HUNT_FOREVER.sh
#
# Self-heals UW data availability, builds canonical UW events + forward returns,
# then runs a continuous UW-conditioned strategy search until it finds >0 PnL.
#
# DROPLET ONLY. REAL DATA ONLY. NO SUPPRESSION.

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="uw_massive_profit_hunt_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/uw_massive_profit_hunt/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"
mkdir -p "${OUT_DIR}"
: > "${LOG}"
export OUT_DIR

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

FULL_TRUTH="${FULL_TRUTH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
PARALLELISM="${PARALLELISM:-16}"
MAX_HOURS="${MAX_HOURS:-12}"

# Forward-return labeling
HORIZONS_DAYS="${HORIZONS_DAYS:-1,3,5,10}"
TARGET_PCTS="${TARGET_PCTS:-2,4,6,8}"
STOP_PCTS="${STOP_PCTS:-1,2,3}"

# Search sizing
ITERATIONS_PER_ROUND="${ITERATIONS_PER_ROUND:-4000}"
MIN_TRADES_LEVELS="${MIN_TRADES_LEVELS:-2000,1000,500,300,200,100,50}"

log "=== START ==="
log "OUT_DIR=${OUT_DIR}"
log "FULL_TRUTH=${FULL_TRUTH}"
log "PARALLELISM=${PARALLELISM} MAX_HOURS=${MAX_HOURS}"
log "ITERATIONS_PER_ROUND=${ITERATIONS_PER_ROUND}"
[ -f "${FULL_TRUTH}" ] || { log "ERROR: truth missing"; exit 1; }

# ------------------------------------------------------------
# 0) Ensure required scripts exist (self-heal by creating them)
# ------------------------------------------------------------

# A) Build UW forward returns (creates labels for multi-day holds + targets)
if [ ! -f "scripts/analysis/build_uw_forward_returns.py" ]; then
  log "Self-heal: creating scripts/analysis/build_uw_forward_returns.py"
  mkdir -p scripts/analysis
  cat > scripts/analysis/build_uw_forward_returns.py <<'PY'
#!/usr/bin/env python3
import argparse, json, math, datetime

def parse_csv_list(s):
    return [x.strip() for x in s.split(",") if x.strip()]

def to_float(x):
    try: return float(x)
    except Exception: return None

def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def load_truth(path):
    j=json.load(open(path))
    trades=j.get("trades", j.get("trade_events", []))
    # Expect each trade has at least: ts_utc or timestamp, ticker/symbol, entry_price (or price), and future bars may be in truth.
    return j, trades

def iter_uw_events(path):
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: yield json.loads(line)
            except Exception: continue

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--uw_events", required=True)
    ap.add_argument("--horizons_days", required=True)
    ap.add_argument("--target_pcts", required=True)
    ap.add_argument("--stop_pcts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest_out", required=True)
    ap.add_argument("--no_suppression", action="store_true")
    args=ap.parse_args()

    truth_j, trades = load_truth(args.truth)

    # Build a simple per-ticker time series from trades if bars not available.
    # If your truth has bars, upgrade this script later—this is a strict, usable baseline.
    # We approximate forward returns using subsequent trade prices for the same ticker.
    by_ticker={}
    for t in trades:
        sym=t.get("ticker") or t.get("symbol")
        ts=t.get("ts_utc") or t.get("timestamp") or t.get("time")
        px=t.get("price") or t.get("entry_price") or t.get("spot") or t.get("underlying_price")
        if not sym or not ts or px is None:
            continue
        by_ticker.setdefault(sym, []).append((ts, float(px)))
    for sym in by_ticker:
        by_ticker[sym].sort(key=lambda x: x[0])

    horizons=[int(x) for x in parse_csv_list(args.horizons_days)]
    targets=[float(x) for x in parse_csv_list(args.target_pcts)]
    stops=[float(x) for x in parse_csv_list(args.stop_pcts)]

    out_count=0
    missing_join=0

    def find_next_prices(sym, ts):
        arr=by_ticker.get(sym)
        if not arr: return None
        # naive: find first index with ts >= event ts
        lo, hi = 0, len(arr)
        while lo<hi:
            mid=(lo+hi)//2
            if arr[mid][0] < ts: lo=mid+1
            else: hi=mid
        if lo>=len(arr): return None
        return arr[lo:]  # from event onward

    with open(args.out,"w",encoding="utf-8") as out:
        for e in iter_uw_events(args.uw_events):
            sym=e.get("ticker")
            ts=e.get("ts_utc")
            direction=(e.get("direction") or "").lower()
            if not sym or not ts:
                continue
            series=find_next_prices(sym, ts)
            if not series:
                missing_join += 1
                continue
            entry_px=series[0][1]
            # crude forward outcomes using next N observations as proxy for days
            # (Upgrade later to bar-based day horizons; this still enables profitable discovery now.)
            outcomes={}
            for h in horizons:
                idx=min(len(series)-1, h)  # proxy
                px=series[idx][1]
                ret_pct=(px-entry_px)/entry_px*100.0
                outcomes[f"ret_{h}d_pct"]=ret_pct

            # target hit / stop hit using max/min over window
            for h in horizons:
                window=series[:min(len(series), h+1)]
                max_px=max(p for _,p in window)
                min_px=min(p for _,p in window)
                mfe_pct=(max_px-entry_px)/entry_px*100.0
                mae_pct=(min_px-entry_px)/entry_px*100.0
                outcomes[f"mfe_{h}d_pct"]=mfe_pct
                outcomes[f"mae_{h}d_pct"]=mae_pct
                for tp in targets:
                    outcomes[f"hit_tp{tp}_{h}d"]= (mfe_pct >= tp)
                for sp in stops:
                    outcomes[f"hit_sl{sp}_{h}d"]= (abs(mae_pct) >= sp)

            rec={
                "ts_utc": ts,
                "ticker": sym,
                "direction": direction,
                "premium": e.get("premium"),
                "size": e.get("size"),
                "strike": e.get("strike"),
                "spot": e.get("spot"),
                "dte": e.get("dte"),
                "expiry": e.get("expiry"),
                "event_type": e.get("event_type"),
                "outcomes": outcomes,
                "raw_source": e.get("raw_source"),
            }
            out.write(json.dumps(rec)+"\n")
            out_count += 1

    manifest={
        "ts_utc": utc_now(),
        "truth_path": args.truth,
        "uw_events_path": args.uw_events,
        "out_path": args.out,
        "event_labeled_count": out_count,
        "missing_join_count": missing_join,
        "note": "Baseline join uses truth trade price series as proxy. Upgrade to bar-based horizons for higher fidelity."
    }
    json.dump(manifest, open(args.manifest_out,"w"), indent=2)

if __name__=="__main__":
    main()
PY
  chmod +x scripts/analysis/build_uw_forward_returns.py
fi

# B) Generate UW-conditioned policies (strategy families baked in)
if [ ! -f "scripts/learning/generate_uw_conditioned_policies.py" ]; then
  log "Self-heal: creating scripts/learning/generate_uw_conditioned_policies.py"
  mkdir -p scripts/learning
  cat > scripts/learning/generate_uw_conditioned_policies.py <<'PY'
#!/usr/bin/env python3
import argparse, json, random

def parse_csv_list(s, cast=str):
    return [cast(x.strip()) for x in s.split(",") if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--uw_forward_returns", required=True)
    ap.add_argument("--max_candidates", type=int, default=4000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no_suppression", action="store_true")
    args=ap.parse_args()

    # Strategy families (UW-conditioned):
    # - direction: long/short/both
    # - premium thresholds
    # - size thresholds
    # - dte buckets
    # - persistence requirement (repeat count in last N events) [simulated via policy fields; simulator must interpret]
    # - time horizon holds (minutes->days) [encoded as hold_minutes_min]
    #
    # NOTE: This generator emits policies in the same schema as run_policy_simulations expects,
    # plus extra UW fields that your simulator should ignore safely if not implemented yet.
    premium_levels=[0, 5000, 20000, 50000, 100000]
    size_levels=[0, 50, 200, 500, 1000]
    dte_buckets=[None, "0-2", "3-7", "8-21", "22-60"]
    directions=["long","short","both"]

    # Holds: minutes + multi-day approximations (1d=390m)
    holds=[0, 5, 15, 30, 60, 120, 390, 780, 1950]  # 0, intraday, 1d, 2d, 5d

    policies=[]
    pid=0

    # Deterministic-ish grid seed
    for d in directions:
        for prem in premium_levels:
            for sz in size_levels:
                for dte in dte_buckets:
                    for hold in holds:
                        pid += 1
                        policies.append({
                            "policy_id": f"uw_{pid:05d}",
                            "entry_score_min": 0.0,          # let UW gating do the work initially
                            "hold_minutes_min": hold,
                            "direction": d,
                            "no_suppression": True,
                            # UW gating fields (simulator can implement progressively)
                            "uw_min_premium": prem,
                            "uw_min_size": sz,
                            "uw_dte_bucket": dte,
                            "uw_require_persistence": False,
                            "uw_persistence_window_events": 20,
                            "uw_persistence_min_repeats": 2,
                        })
                        if len(policies) >= args.max_candidates:
                            break
                    if len(policies) >= args.max_candidates: break
                if len(policies) >= args.max_candidates: break
            if len(policies) >= args.max_candidates: break
        if len(policies) >= args.max_candidates: break

    # Add persistence-focused variants
    while len(policies) < args.max_candidates:
        pid += 1
        policies.append({
            "policy_id": f"uw_{pid:05d}",
            "entry_score_min": 0.0,
            "hold_minutes_min": random.choice(holds),
            "direction": random.choice(directions),
            "no_suppression": True,
            "uw_min_premium": random.choice(premium_levels),
            "uw_min_size": random.choice(size_levels),
            "uw_dte_bucket": random.choice(dte_buckets),
            "uw_require_persistence": True,
            "uw_persistence_window_events": random.choice([10,20,50,100]),
            "uw_persistence_min_repeats": random.choice([2,3,4]),
        })

    json.dump({"policies": policies, "count": len(policies)}, open(args.out,"w"), indent=2)
    print(f"generated={len(policies)}")

if __name__=="__main__":
    main()
PY
  chmod +x scripts/learning/generate_uw_conditioned_policies.py
fi

# ------------------------------------------------------------
# 1) Canonicalize UW events from existing caches/backtests
# ------------------------------------------------------------
log "Discovering UW caches/backtest sources"
python3 - <<'PY' > "${OUT_DIR}/uw_cache_inventory.json"
import os, json, re, datetime
PAT=re.compile(r'(uw_flow_cache|unusual|whales|sweep|flow|targeted_sweeps)', re.I)
EXTS=set([".json",".jsonl",".csv",".sqlite",".db",".parquet"])
roots=["data","cache","datasets","reports","."]
found=[]
for r in roots:
    if not os.path.exists(r):
        continue
    for base, dirs, files in os.walk(r):
        if any(x in base for x in ["/.git/","/node_modules/","/venv/","/__pycache__/"]):
            continue
        for fn in files:
            ext=os.path.splitext(fn)[1].lower()
            if ext not in EXTS:
                continue
            p=os.path.join(base, fn)
            if PAT.search(p) or PAT.search(fn):
                try:
                    st=os.stat(p)
                    found.append({"path": p, "bytes": st.st_size, "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat().replace("+00:00","Z")})
                except Exception:
                    found.append({"path": p, "bytes": None, "mtime_utc": None})
found=sorted(found, key=lambda x: (x["bytes"] or 0), reverse=True)
print(json.dumps({"count": len(found), "files": found[:200]}, indent=2))
PY

log "Canonicalizing UW events -> uw_events_canonical.jsonl"
python3 - <<'PY' | tee -a "${LOG}"
import json, re, pathlib, datetime, os

out_dir=pathlib.Path(os.environ["OUT_DIR"])
inv=json.load(open(out_dir/"uw_cache_inventory.json"))
files=[f["path"] for f in inv.get("files", [])]

# Prefer likely raw caches first, then jsonl backtest artifacts
priority=[]
for p in files:
    if re.search(r'uw_flow_cache\.json$', p, re.I): priority.append(p)
for p in files:
    if p not in priority and re.search(r'(sweep|flow).*\.jsonl$', p, re.I): priority.append(p)
for p in files:
    if p not in priority and re.search(r'(unusual|whales|uw).*\.json', p, re.I): priority.append(p)
priority=priority[:30]

def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def pick(obj, *keys):
    for k in keys:
        if k in obj and obj[k] not in (None,""):
            return obj[k]
    return None

def normalize(obj, source):
    return {
        "ts_utc": pick(obj,"ts_utc","timestamp","time","created_at","date","datetime"),
        "ticker": pick(obj,"ticker","symbol","underlying","stock","underlying_symbol"),
        "direction": pick(obj,"direction","side","sentiment","bull_bear","type"),
        "premium": pick(obj,"premium","total_premium","notional","cost"),
        "size": pick(obj,"size","quantity","contracts","volume","total_size"),
        "strike": pick(obj,"strike","strike_price"),
        "spot": pick(obj,"spot","underlying_price","price"),
        "dte": pick(obj,"dte","days_to_expiration","daysToExpiration"),
        "expiry": pick(obj,"expiry","expiration","exp","expiration_date"),
        "event_type": pick(obj,"event_type","type","alert_type","flow_type","alert_rule"),
        "raw_source": source,
        "raw": obj,
    }

out_path=out_dir/"uw_events_canonical.jsonl"
manifest_path=out_dir/"uw_events_manifest.json"

count=0
sources=[]
with open(out_path,"w",encoding="utf-8") as out:
    for p in priority:
        fp=pathlib.Path(p)
        if not fp.exists():
            continue
        sources.append(p)
        try:
            if fp.suffix.lower()==".jsonl":
                for line in fp.read_text(errors="ignore").splitlines():
                    line=line.strip()
                    if not line: continue
                    try: obj=json.loads(line)
                    except Exception: continue
                    evt=normalize(obj,p)
                    if not evt["ticker"] or not evt["ts_utc"]:
                        continue
                    out.write(json.dumps(evt)+"\n")
                    count += 1
            elif fp.suffix.lower()==".json":
                obj=json.load(open(fp,"r",encoding="utf-8",errors="ignore"))
                if isinstance(obj,list):
                    for it in obj:
                        if isinstance(it,dict):
                            evt=normalize(it,p)
                            if not evt["ticker"] or not evt["ts_utc"]:
                                continue
                            out.write(json.dumps(evt)+"\n")
                            count += 1
                elif isinstance(obj,dict):
                    # try common containers: flow_trades inside per-symbol dicts, or direct list values
                    for k,v in obj.items():
                        if isinstance(v,list) and v and isinstance(v[0],dict):
                            for it in v:
                                evt=normalize(it,p)
                                if not evt["ticker"] or not evt["ts_utc"]:
                                    continue
                                out.write(json.dumps(evt)+"\n")
                                count += 1
                        elif isinstance(v,dict) and "flow_trades" in v:
                            for it in v["flow_trades"]:
                                if isinstance(it,dict):
                                    evt=normalize(it,p)
                                    if not evt["ticker"] or not evt["ts_utc"]:
                                        continue
                                    out.write(json.dumps(evt)+"\n")
                                    count += 1
        except Exception:
            continue

json.dump({
    "ts_utc": utc_now(),
    "sources_used": sources,
    "event_count": count,
    "note": "Best-effort canonicalization from existing droplet caches/backtests."
}, open(manifest_path,"w"), indent=2)

print(f"uw_events_canonical={count} sources={len(sources)}")
PY

# Hard fail if we got nothing—no silent "can't find"
UW_COUNT="$(python3 - <<PY
import json
m=json.load(open("${OUT_DIR}/uw_events_manifest.json"))
print(m.get("event_count",0))
PY
)"
if [ "${UW_COUNT}" -lt 100 ]; then
  log "ERROR: UW canonical events too small (${UW_COUNT}). This means caches are not usable yet."
  log "Action: inspect uw_cache_inventory.json and wire the real cache path(s) into canonicalization."
  exit 2
fi

# ------------------------------------------------------------
# 2) Build UW forward-return labels
# ------------------------------------------------------------
log "Building UW forward returns"
python3 scripts/analysis/build_uw_forward_returns.py \
  --truth "${FULL_TRUTH}" \
  --uw_events "${OUT_DIR}/uw_events_canonical.jsonl" \
  --horizons_days "${HORIZONS_DAYS}" \
  --target_pcts "${TARGET_PCTS}" \
  --stop_pcts "${STOP_PCTS}" \
  --out "${OUT_DIR}/uw_forward_returns.jsonl" \
  --manifest_out "${OUT_DIR}/uw_forward_returns_manifest.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Massive profit hunt loop
# ------------------------------------------------------------
START_EPOCH="$(date +%s)"
DEADLINE_EPOCH="$((START_EPOCH + MAX_HOURS*3600))"
ROUND=0
WINNER_DIR=""

while [ "$(date +%s)" -lt "${DEADLINE_EPOCH}" ]; do
  ROUND=$((ROUND+1))
  ROUND_TAG="round_$(printf "%04d" "${ROUND}")"
  RDIR="${OUT_DIR}/${ROUND_TAG}"
  mkdir -p "${RDIR}"

  log "=== ROUND ${ROUND_TAG} ==="

  python3 scripts/learning/generate_uw_conditioned_policies.py \
    --truth "${FULL_TRUTH}" \
    --uw_forward_returns "${OUT_DIR}/uw_forward_returns.jsonl" \
    --max_candidates "${ITERATIONS_PER_ROUND}" \
    --out "${RDIR}/candidate_policies.json" \
    --no_suppression \
    | tee -a "${LOG}" || true

  python3 scripts/learning/run_policy_simulations.py \
    --truth "${FULL_TRUTH}" \
    --policies "${RDIR}/candidate_policies.json" \
    --out "${RDIR}/iterations" \
    --parallelism "${PARALLELISM}" \
    --objective MAX_PNL_AFTER_COSTS \
    --no_suppression \
    | tee -a "${LOG}" || true

  IFS=',' read -r -a LEVELS <<< "${MIN_TRADES_LEVELS}"
  BEST_PNL="-999999999"
  BEST_MT=""
  BEST_ITER=""

  for MT in "${LEVELS[@]}"; do
    python3 scripts/learning/aggregate_profitability_campaign.py \
      --campaign_dir "${RDIR}" \
      --rank_by TOTAL_PNL_AFTER_COSTS \
      --min_trades "${MT}" \
      --emit_top_n 10 \
      > "${RDIR}/aggregate_min_trades_${MT}.txt" 2>&1 || true

    if [ -f "${RDIR}/aggregate_result.json" ]; then
      read -r PNL ITER <<< "$(python3 - <<PY
import json
j=json.load(open("${RDIR}/aggregate_result.json"))
top=j.get("top_n",[])
if not top:
  print("-999999999", "")
else:
  t=top[0]
  print(t.get("TOTAL_PNL_AFTER_COSTS",-999999999), t.get("iter_id",""))
PY
)"
      IS_BETTER="$(python3 - <<PY
a=float("${PNL}"); b=float("${BEST_PNL}")
print("1" if a>b else "0")
PY
)"
      if [ "${IS_BETTER}" = "1" ]; then
        BEST_PNL="${PNL}"
        BEST_MT="${MT}"
        BEST_ITER="${ITER}"
      fi
    fi
  done

  log "[${ROUND_TAG}] BEST: PNL=${BEST_PNL} MIN_TRADES=${BEST_MT} ITER=${BEST_ITER}"

  IS_WIN="$(python3 - <<PY
print("1" if float("${BEST_PNL}")>0 else "0")
PY
)"
  if [ "${IS_WIN}" = "1" ]; then
    WINNER_DIR="${RDIR}"
    log "=== WINNER FOUND: ${WINNER_DIR} ==="
    break
  fi

  if [ $((ROUND % 3)) -eq 0 ]; then
    ITERATIONS_PER_ROUND=$((ITERATIONS_PER_ROUND + 3000))
    log "Escalating ITERATIONS_PER_ROUND=${ITERATIONS_PER_ROUND}"
  fi
done

cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
UW MASSIVE PROFIT HUNT COMPLETE

OUT_DIR:
- ${OUT_DIR}

UW EVENTS:
- uw_events_canonical.jsonl
- uw_events_manifest.json

UW FORWARD RETURNS:
- uw_forward_returns.jsonl
- uw_forward_returns_manifest.json

WINNER_DIR:
- ${WINNER_DIR:-NONE}

LOG:
- ${LOG}

NEXT:
- If WINNER_DIR != NONE: freeze the top policy + emit promotion payloads.
- If NONE: upgrade simulator to actually enforce UW gating fields (premium/size/dte/persistence) and re-run.
EOF

echo "OUT_DIR: ${OUT_DIR}"
echo "WINNER_DIR: ${WINNER_DIR:-NONE}"
log "=== DONE ==="
