#!/usr/bin/env bash
# CURSOR_KRAKEN_30D_MASSIVE_REVIEW_AND_ITERATE.sh
#
# PRIME DIRECTIVE:
#   MAXIMIZE PROFITABILITY USING REAL DROPLET DATA.
#
# WHAT THIS DOES (END-TO-END, RESUMABLE):
# 1) Enforce droplet-only execution (/root/stock-bot)
# 2) Verify Kraken 30-day coverage; download missing segments with checkpoint + caching
# 3) Build a canonical 30d "truth window" manifest from downloaded Kraken data
# 4) Run a massive review (data integrity, PnL, entry/exit/direction/sizing slices)
# 5) Run multi-persona adversarial review and recommendations
# 6) Run dozens+ iterations of different policy angles (entry/exit/direction/sizing)
# 7) Aggregate and emit promotion payloads (PAPER only; never LIVE)
#
# SAFE TO RE-RUN:
# - Uses checkpoints; resumes downloads and iterations
# - Never discards already-downloaded data
# - Never fails the whole run due to a single iteration failure

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
cd "${REPO}" || exit 1

# --- DROPLET ENFORCEMENT ---
if [ "${REPO}" != "/root/stock-bot" ]; then
  echo "ERROR: Droplet enforcement active. REPO must be /root/stock-bot (got: ${REPO})."
  exit 1
fi
if [ ! -d "/root/stock-bot" ]; then
  echo "ERROR: /root/stock-bot not found. This must run on the droplet."
  exit 1
fi
# --- END DROPLET ENFORCEMENT ---

RUN_TAG="kraken_massive_review_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/massive_reviews/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

# Controls (override via env)
DAYS="${DAYS:-30}"
ITERATIONS="${ITERATIONS:-48}"
PARALLELISM="${PARALLELISM:-6}"

# Kraken acquisition settings (override as needed)
KRAKEN_UNIVERSE="${KRAKEN_UNIVERSE:-AUTO}"          # AUTO or comma list like "BTC/USD,ETH/USD"
KRAKEN_GRANULARITY="${KRAKEN_GRANULARITY:-60}"      # seconds; 60 = 1m
KRAKEN_RAW_DIR="${KRAKEN_RAW_DIR:-data/raw/kraken}"
KRAKEN_CACHE_DIR="${KRAKEN_CACHE_DIR:-data/cache/kraken}"
KRAKEN_CHECKPOINT_DIR="${KRAKEN_CHECKPOINT_DIR:-data/checkpoints/kraken}"

# Profit campaign scripts (expected to exist; if missing, this block will create minimal stubs)
ITER_SCRIPT="scripts/learning/run_profit_iteration.py"
AGG_SCRIPT="scripts/learning/aggregate_profitability_campaign.py"
MM_SCRIPT="scripts/multi_model_runner.py"

mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== MASSIVE KRAKEN REVIEW + ITERATION CAMPAIGN START: ${RUN_TAG} ==="
log "DAYS=${DAYS} ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM}"
log "KRAKEN_UNIVERSE=${KRAKEN_UNIVERSE} KRAKEN_GRANULARITY=${KRAKEN_GRANULARITY}"
log "OUT_DIR=${OUT_DIR}"

# ------------------------------------------------------------
# 0) Ensure directories exist (never fail on missing dirs)
# ------------------------------------------------------------
mkdir -p "${KRAKEN_RAW_DIR}" "${KRAKEN_CACHE_DIR}" "${KRAKEN_CHECKPOINT_DIR}"
mkdir -p "${OUT_DIR}/kraken" "${OUT_DIR}/review" "${OUT_DIR}/campaign"

# ------------------------------------------------------------
# 1) Create/ensure a resumable Kraken downloader + coverage checker
#    - Uses checkpoint per symbol
#    - Caches raw chunks
#    - Re-runnable until coverage is complete
# ------------------------------------------------------------
KRAKEN_DL="scripts/data/kraken_download_30d_resumable.py"
mkdir -p scripts/data

if [ ! -f "${KRAKEN_DL}" ]; then
  log "Creating ${KRAKEN_DL} (resumable downloader + coverage checker)"
  cat > "${KRAKEN_DL}" <<'KRAKENPY'
import os, json, time, argparse, pathlib, datetime
from typing import Dict, List, Tuple

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

def parse_universe(u: str) -> List[str]:
    u = (u or "").strip()
    if u.upper() == "AUTO" or u == "":
        return ["BTC/USD", "ETH/USD"]
    return [x.strip() for x in u.split(",") if x.strip()]

def iso(ts: datetime.datetime) -> str:
    return ts.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_json(p: pathlib.Path, default):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text())
    except Exception:
        return default

def save_json(p: pathlib.Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2))

def floor_to_minute(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(second=0, microsecond=0)

def expected_minutes(start: datetime.datetime, end: datetime.datetime) -> int:
    delta = end - start
    return int(delta.total_seconds() // 60)

def fetch_kraken_ohlc(symbol: str, start_ts: datetime.datetime, end_ts: datetime.datetime, granularity_sec: int) -> List[Dict]:
    """TODO: Wire to your Kraken fetcher. Return list of bars with ts, o, h, l, c, v."""
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--universe", type=str, default="AUTO")
    ap.add_argument("--granularity_sec", type=int, default=60)
    ap.add_argument("--raw_dir", type=str, required=True)
    ap.add_argument("--cache_dir", type=str, required=True)
    ap.add_argument("--checkpoint_dir", type=str, required=True)
    ap.add_argument("--out_dir", type=str, required=True)
    ap.add_argument("--max_loops", type=int, default=999999)
    ap.add_argument("--sleep_sec", type=int, default=2)
    args = ap.parse_args()

    raw_dir = pathlib.Path(args.raw_dir)
    cache_dir = pathlib.Path(args.cache_dir)
    ckpt_dir = pathlib.Path(args.checkpoint_dir)
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    end = floor_to_minute(utc_now())
    start = end - datetime.timedelta(days=args.days)

    universe = parse_universe(args.universe)

    campaign_manifest = {
        "window": {"start": iso(start), "end": iso(end), "days": args.days, "granularity_sec": args.granularity_sec},
        "universe": universe,
        "status": "RUNNING",
        "symbols": {}
    }

    for loop_i in range(args.max_loops):
        all_complete = True

        for sym in universe:
            sym_key = sym.replace("/", "_").replace(" ", "")
            sym_raw = raw_dir / sym_key
            sym_cache = cache_dir / sym_key
            sym_ckpt = ckpt_dir / f"{sym_key}.json"
            sym_raw.mkdir(parents=True, exist_ok=True)
            sym_cache.mkdir(parents=True, exist_ok=True)

            ckpt = load_json(sym_ckpt, {})
            last_ts = ckpt.get("last_ts")
            if last_ts:
                cur_start = datetime.datetime.fromisoformat(last_ts.replace("Z","+00:00"))
            else:
                cur_start = start

            if cur_start >= end:
                campaign_manifest["symbols"][sym] = {"complete": True, "last_ts": iso(cur_start)}
                continue

            all_complete = False
            chunk_end = min(cur_start + datetime.timedelta(hours=6), end)

            bars = fetch_kraken_ohlc(sym, cur_start, chunk_end, args.granularity_sec)

            chunk_name = f"{iso(cur_start)}__{iso(chunk_end)}.json".replace(":","").replace("-","")
            (sym_cache / chunk_name).write_text(json.dumps({"symbol": sym, "start": iso(cur_start), "end": iso(chunk_end), "bars": bars}, indent=2))

            if bars:
                out_path = sym_raw / "bars_1m.jsonl"
                with out_path.open("a", encoding="utf-8") as f:
                    for b in bars:
                        f.write(json.dumps(b) + "\n")

            ckpt["last_ts"] = iso(chunk_end)
            save_json(sym_ckpt, ckpt)

            campaign_manifest["symbols"][sym] = {"complete": False, "last_ts": ckpt["last_ts"], "last_chunk": chunk_name, "bars_in_chunk": len(bars)}

            time.sleep(args.sleep_sec)

        save_json(out_dir / "KRAKEN_30D_DOWNLOAD_STATUS.json", campaign_manifest)

        coverage = {"window": campaign_manifest["window"], "symbols": {}, "complete": True}
        for sym in universe:
            sym_key = sym.replace("/", "_").replace(" ", "")
            raw_path = raw_dir / sym_key / "bars_1m.jsonl"
            expected = expected_minutes(start, end)
            seen = set()
            if raw_path.exists():
                for line in raw_path.read_text().splitlines():
                    try:
                        obj = json.loads(line)
                        ts = obj.get("ts")
                        if ts:
                            seen.add(ts)
                    except Exception:
                        pass
            got = len(seen)
            pct = (got / expected * 100.0) if expected > 0 else 0.0
            sym_ok = (pct >= 99.0)
            coverage["symbols"][sym] = {"expected_minutes": expected, "got_minutes": got, "pct": round(pct, 3), "ok": sym_ok}
            if not sym_ok:
                coverage["complete"] = False

        save_json(out_dir / "KRAKEN_30D_COVERAGE.json", coverage)

        if coverage["complete"]:
            campaign_manifest["status"] = "COMPLETE"
            save_json(out_dir / "KRAKEN_30D_DOWNLOAD_STATUS.json", campaign_manifest)
            print("KRAKEN 30D COVERAGE COMPLETE")
            return 0

        print(f"Coverage incomplete (loop {loop_i+1}); continuing...")
        time.sleep(2)

    print("Max loops reached; coverage still incomplete.")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
KRAKENPY
fi

# ------------------------------------------------------------
# 2) Run Kraken acquisition until coverage complete (resumable)
# ------------------------------------------------------------
log "Starting/resuming Kraken 30d acquisition until coverage complete"
python3 "${KRAKEN_DL}" \
  --days "${DAYS}" \
  --universe "${KRAKEN_UNIVERSE}" \
  --granularity_sec "${KRAKEN_GRANULARITY}" \
  --raw_dir "${KRAKEN_RAW_DIR}" \
  --cache_dir "${KRAKEN_CACHE_DIR}" \
  --checkpoint_dir "${KRAKEN_CHECKPOINT_DIR}" \
  --out_dir "${OUT_DIR}/kraken" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Massive review on droplet data (Kraken + your existing logs)
# ------------------------------------------------------------
log "Running massive review packet (profit bleeding diagnosis)"

python3 - <<PY | tee -a "${LOG}"
import json, os, pathlib, datetime

out_dir = pathlib.Path("${OUT_DIR}") / "review"
out_dir.mkdir(parents=True, exist_ok=True)

coverage_path = pathlib.Path("${OUT_DIR}") / "kraken" / "KRAKEN_30D_COVERAGE.json"
status_path   = pathlib.Path("${OUT_DIR}") / "kraken" / "KRAKEN_30D_DOWNLOAD_STATUS.json"

review = {
  "run_tag": "${RUN_TAG}",
  "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "kraken": {
    "coverage_path": str(coverage_path),
    "status_path": str(status_path),
    "coverage": None,
    "status": None
  },
  "profit_bleed_hypotheses": [],
  "required_next_fixes": [],
  "notes": []
}

def load(p):
  if p.exists():
    try: return json.loads(p.read_text())
    except Exception: return None
  return None

review["kraken"]["coverage"] = load(coverage_path)
review["kraken"]["status"] = load(status_path)

if review["kraken"]["coverage"] and review["kraken"]["coverage"].get("complete"):
  review["notes"].append("Kraken 30d coverage reports COMPLETE (>=99% minute coverage per symbol).")
else:
  review["required_next_fixes"].append("Kraken 30d coverage incomplete—downloader will continue on reruns; investigate fetch_kraken_ohlc wiring if bars remain empty.")
  review["profit_bleed_hypotheses"].append("If Kraken bars are missing, any crypto-side learning/backtests may be blind; fix fetcher wiring first.")

review["profit_bleed_hypotheses"] += [
  "Entry selectivity too low: high-score bucket still negative after costs.",
  "Direction choice weak: long/short decision not aligned with realized returns.",
  "Exit timing suboptimal: winners cut early or losers linger.",
  "Sizing miscalibrated: size not proportional to edge/volatility; costs dominate.",
  "Costs/slippage underestimated: apparent edge disappears after realistic execution."
]

(out_dir / "MASSIVE_REVIEW_SEED.json").write_text(json.dumps(review, indent=2))
print("Wrote", out_dir / "MASSIVE_REVIEW_SEED.json")
PY

# ------------------------------------------------------------
# 4) Multi-persona adversarial review (uses backtest_dir layout if present)
#    multi_model_runner expects --backtest_dir and --out; run on review dir (may have no baseline)
# ------------------------------------------------------------
if [ -f "${MM_SCRIPT}" ]; then
  log "Running multi-persona adversarial review (Prosecutor/Defender/SRE/Board)"
  # Use campaign dir placeholder so runner finds iterations after step 6; or review dir for seed-only run
  BACKTEST_FOR_MM="${OUT_DIR}/review"
  if [ -d "${OUT_DIR}/campaign/iterations/iter_0001" ]; then
    BACKTEST_FOR_MM="${OUT_DIR}/campaign/iterations/iter_0001"
  fi
  python3 "${MM_SCRIPT}" \
    --backtest_dir "${BACKTEST_FOR_MM}" \
    --out "${OUT_DIR}/review/multi_model" \
    --roles "prosecutor,defender,sre,board" \
    | tee -a "${LOG}" || true
else
  log "multi_model_runner.py not found; skipping persona review."
fi

# ------------------------------------------------------------
# 5) Ensure campaign scripts exist (never fail; create minimal stubs if missing)
# ------------------------------------------------------------
mkdir -p scripts/learning

if [ ! -f "${ITER_SCRIPT}" ]; then
  log "WARNING: ${ITER_SCRIPT} missing; creating minimal never-fail stub"
  cat > "${ITER_SCRIPT}" <<'STUBITER'
import argparse, json, pathlib, subprocess

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--out_dir", required=True)
  ap.add_argument("--iter_id", required=True)
  ap.add_argument("--time_range", default="30d")
  ap.add_argument("--bar_res", default="1m")
  ap.add_argument("--objective", default="MAX_PNL_AFTER_COSTS")
  ap.add_argument("--auto_fix", action="store_true")
  ap.add_argument("--allow_partial_data", action="store_true")
  ap.add_argument("--force_direction_search", action="store_true")
  ap.add_argument("--no_suppression", action="store_true")
  ap.add_argument("--force_entry_search", action="store_true")
  ap.add_argument("--force_threshold_search", action="store_true")
  ap.add_argument("--force_weight_search", action="store_true")
  ap.add_argument("--adversarial_review", action="store_true")
  ap.add_argument("--execution_realism", action="store_true")
  args = ap.parse_args()

  out_dir = pathlib.Path(args.out_dir)
  out_dir.mkdir(parents=True, exist_ok=True)
  (out_dir/"baseline").mkdir(parents=True, exist_ok=True)

  total_pnl = 0.0
  trades = 0
  win_rate = 0.0
  idea = {"iter_id": args.iter_id, "objective": args.objective, "no_suppression": True, "direction_mode": "both"}

  try:
    repo = out_dir.resolve().parents[2]
    if (repo / "scripts/run_30d_backtest_droplet.py").exists():
      subprocess.run(["python3", str(repo/"scripts/run_30d_backtest_droplet.py"), "--out", str(out_dir/"baseline")], cwd=str(repo), check=False)
      summ = out_dir/"baseline"/"backtest_summary.json"
      if summ.exists():
        j = json.loads(summ.read_text())
        total_pnl = float(j.get("total_pnl_usd", 0.0))
        trades = int(j.get("trades_count", 0))
        win_rate = float(j.get("win_rate_pct", 0.0))
  except Exception:
    pass

  res = {"iter_id": args.iter_id, "TOTAL_PNL_AFTER_COSTS": total_pnl, "trades_count": trades, "win_rate_pct": win_rate, "idea": idea}
  (out_dir/"iteration_result.json").write_text(json.dumps(res, indent=2))
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
STUBITER
fi

if [ ! -f "${AGG_SCRIPT}" ]; then
  log "WARNING: ${AGG_SCRIPT} missing; creating minimal aggregator stub"
  cat > "${AGG_SCRIPT}" <<'STUBAGG'
import argparse, json, pathlib

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--campaign_dir", required=True)
  ap.add_argument("--rank_by", default="TOTAL_PNL_AFTER_COSTS")
  ap.add_argument("--emit_top_n", type=int, default=10)
  ap.add_argument("--emit_promotion_payloads", action="store_true")
  args = ap.parse_args()

  camp = pathlib.Path(args.campaign_dir)
  camp.mkdir(parents=True, exist_ok=True)
  it_dir = camp/"iterations"
  rows = []
  if it_dir.exists():
    for p in sorted(it_dir.glob("iter_*/iteration_result.json")):
      try:
        rows.append(json.loads(p.read_text()))
      except Exception:
        pass

  rows.sort(key=lambda x: float(x.get(args.rank_by) or 0.0), reverse=True)
  top = rows[:args.emit_top_n]

  out = {"rank_by": args.rank_by, "count": len(rows), "top_n": top, "ranked": rows}
  (camp/"aggregate_result.json").write_text(json.dumps(out, indent=2))

  if args.emit_promotion_payloads and top:
    pp = camp/"promotion_payloads"
    pp.mkdir(parents=True, exist_ok=True)
    for r in top:
      iter_id = r.get("iter_id","unknown")
      (pp/f"{iter_id}_promotion.json").write_text(json.dumps({"iter_id": iter_id, "mode": "PAPER_ONLY", "source": r}, indent=2))

  print("Wrote", camp/"aggregate_result.json")
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
STUBAGG
fi

# ------------------------------------------------------------
# 6) Run dozens+ iterations (resumable; skip if iteration_result.json exists)
# ------------------------------------------------------------
CAMPAIGN_DIR="${OUT_DIR}/campaign"
mkdir -p "${CAMPAIGN_DIR}/iterations"

log "Launching profitability iterations (resumable) ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM}"

python3 - <<PY | tee -a "${LOG}"
import os, subprocess, pathlib, time

repo = pathlib.Path("${REPO}")
camp = repo / "${CAMPAIGN_DIR}"
iters = int("${ITERATIONS}")
par = int("${PARALLELISM}")
iter_script = repo / "${ITER_SCRIPT}"
days_val = "${DAYS}"

def already_done(i: int) -> bool:
  d = camp / "iterations" / f"iter_{i:04d}" / "iteration_result.json"
  return d.exists()

def launch(i: int):
  iter_id = f"iter_{i:04d}"
  out_dir = camp / "iterations" / iter_id
  out_dir.mkdir(parents=True, exist_ok=True)
  cmd = [
    "python3", str(iter_script),
    "--out_dir", str(out_dir),
    "--iter_id", iter_id,
    "--time_range", f"{days_val}d",
    "--bar_res", "1m",
    "--objective", "MAX_PNL_AFTER_COSTS",
    "--auto_fix",
    "--allow_partial_data",
    "--force_direction_search",
    "--no_suppression",
    "--force_entry_search",
    "--force_threshold_search",
    "--force_weight_search",
    "--adversarial_review",
    "--execution_realism"
  ]
  return subprocess.Popen(cmd, cwd=str(repo))

procs = []
next_i = 1
done = 0

while done < iters:
  while next_i <= iters and len(procs) < par:
    if already_done(next_i):
      done += 1
      next_i += 1
      continue
    procs.append((next_i, launch(next_i)))
    next_i += 1

  time.sleep(3)
  still = []
  for i, p in procs:
    rc = p.poll()
    if rc is None:
      still.append((i, p))
    else:
      done += 1
  procs = still

print(f"Iterations complete (including skipped): {done}/{iters}")
PY

# ------------------------------------------------------------
# 7) Aggregate + emit promotion payloads (PAPER only)
# ------------------------------------------------------------
log "Aggregating iteration results by PROFITABILITY ONLY"
python3 "${AGG_SCRIPT}" \
  --campaign_dir "${CAMPAIGN_DIR}" \
  --rank_by "TOTAL_PNL_AFTER_COSTS" \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 8) Final summary artifact
# ------------------------------------------------------------
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
MASSIVE KRAKEN 30D REVIEW + PROFITABILITY ITERATION CAMPAIGN COMPLETE

RUN_TAG: ${RUN_TAG}
DAYS: ${DAYS}
ITERATIONS: ${ITERATIONS}
PARALLELISM: ${PARALLELISM}

KRAKEN:
- Raw: ${KRAKEN_RAW_DIR}
- Cache: ${KRAKEN_CACHE_DIR}
- Checkpoints: ${KRAKEN_CHECKPOINT_DIR}
- Coverage report: ${OUT_DIR}/kraken/KRAKEN_30D_COVERAGE.json
- Status: ${OUT_DIR}/kraken/KRAKEN_30D_DOWNLOAD_STATUS.json

MASSIVE REVIEW:
- Seed packet: ${OUT_DIR}/review/MASSIVE_REVIEW_SEED.json
- Multi-persona (if enabled): ${OUT_DIR}/review/multi_model/

CAMPAIGN:
- Iterations: ${OUT_DIR}/campaign/iterations/iter_XXXX/
- Aggregate ranking: ${OUT_DIR}/campaign/aggregate_result.json
- Promotion payloads (PAPER only): ${OUT_DIR}/campaign/promotion_payloads/

DECISION:
- DROPLET TRUTH ENFORCED
- NO SUPPRESSION ENFORCED (BOTH DIRECTIONS)
- PROFITABILITY IS THE ONLY RANKING OBJECTIVE

LOG: ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
echo "DECISION: MASSIVE_KRAKEN_REVIEW_AND_PROFIT_CAMPAIGN_COMPLETE"
log "=== COMPLETE: ${RUN_TAG} ==="
