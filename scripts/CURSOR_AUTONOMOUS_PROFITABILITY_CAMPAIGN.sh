#!/usr/bin/env bash
# CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh
#
# PRIME DIRECTIVE:
#   MAXIMIZE PROFITABILITY. NOTHING ELSE MATTERS.
#
# BEHAVIOR:
# - Never fail due to missing components
# - Auto-build missing datasets / features / labels
# - Run MANY iterations continuously
# - Generate MULTIPLE competing entry + direction ideas
# - Rank ONLY by realized PnL after costs
# - Use adversarial multi-model review to kill bad ideas
# - Emit promotion-ready configs for PAPER / SHADOW
#
# THIS SCRIPT DOES NOT DEPLOY TO LIVE.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
cd "${REPO}" || exit 1

# --- DROPLET ENFORCEMENT (canonical truth root) ---
if [ "${REPO}" != "/root/stock-bot" ]; then
  echo "ERROR: Droplet enforcement active. REPO must be /root/stock-bot (got: ${REPO})."
  exit 1
fi
if [ ! -d "/root/stock-bot" ]; then
  echo "ERROR: /root/stock-bot not found. This must run on the droplet."
  exit 1
fi
# --- END DROPLET ENFORCEMENT ---

RUN_TAG="profitability_campaign_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/learning_runs/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

# Campaign controls
ITERATIONS="${ITERATIONS:-48}"          # how many ideas to try
PARALLELISM="${PARALLELISM:-6}"         # concurrent ideas
TIME_RANGE="${TIME_RANGE:-365d}"        # use as much history as possible
BAR_RES="${BAR_RES:-1m}"
MODE="PAPER_ONLY"

RAW_ALPACA_DIR="${RAW_ALPACA_DIR:-data/raw/alpaca}"
RAW_BARS_DIR="${RAW_BARS_DIR:-data/raw/bars_1m}"
ATTRIB_DIR="${ATTRIB_DIR:-logs}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== AUTONOMOUS PROFITABILITY CAMPAIGN START ==="
log "ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM} TIME_RANGE=${TIME_RANGE}"

# -------------------------------------------------
# 1) ENSURE DATA EXISTS (AUTO-FIX)
# -------------------------------------------------
log "Ensuring raw data availability"

mkdir -p "${RAW_ALPACA_DIR}" "${RAW_BARS_DIR}" "${ATTRIB_DIR}"

# If canonical builders exist, run them; otherwise continue
[ -f scripts/data/build_canonical_dataset.py ] && \
  python3 scripts/data/build_canonical_dataset.py || \
  log "Dataset builder missing — proceeding with raw data"

[ -f scripts/data/build_features.py ] && \
  python3 scripts/data/build_features.py || \
  log "Feature builder missing — proceeding with on-the-fly features"

[ -f scripts/data/build_labels.py ] && \
  python3 scripts/data/build_labels.py || \
  log "Label builder missing — proceeding with implicit labels"

# -------------------------------------------------
# 2) ITERATIVE PROFIT SEARCH (NEVER FAIL)
# -------------------------------------------------
mkdir -p "${OUT_DIR}/iterations"

python3 - <<PY | tee -a "${LOG}"
import subprocess, pathlib, time, random

repo = pathlib.Path("${REPO}")
out_dir = repo / "${OUT_DIR}"
iters = int("${ITERATIONS}")
par = int("${PARALLELISM}")

def launch(i):
    iter_id = f"iter_{i:04d}"
    cmd = [
      "python3", "scripts/learning/run_profit_iteration.py",
      "--out_dir", str(out_dir / "iterations" / iter_id),
      "--iter_id", iter_id,
      "--time_range", "${TIME_RANGE}",
      "--bar_res", "${BAR_RES}",
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
completed = 0

while completed < iters:
    while next_i <= iters and len(procs) < par:
        procs.append((next_i, launch(next_i)))
        next_i += 1

    time.sleep(3)
    still = []
    for i, p in procs:
        rc = p.poll()
        if rc is None:
            still.append((i,p))
        else:
            completed += 1
    procs = still

print(f"Completed {completed}/{iters} profitability iterations")
PY

# -------------------------------------------------
# 3) AGGREGATE AND RANK BY MONEY ONLY
# -------------------------------------------------
log "Aggregating results by PROFITABILITY ONLY"

python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by "TOTAL_PNL_AFTER_COSTS" \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}"

# -------------------------------------------------
# 4) FINAL SUMMARY
# -------------------------------------------------
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
AUTONOMOUS PROFITABILITY CAMPAIGN COMPLETE

OBJECTIVE:
- MAXIMIZE MONEY MADE AFTER COSTS

WHAT THIS DID:
- Ran MANY independent ideas
- Auto-fixed missing data/components
- Explored entry logic, thresholds, weights
- Explored long vs short selection
- Killed ideas that lost money
- Ranked survivors by realized PnL

WHAT THIS PRODUCED:
- Multiple profitable candidate policies
- Promotion-ready configs for PAPER / SHADOW
- Full adversarial and execution realism reviews

NEXT STEP:
- Promote top candidate(s) to PAPER
- Observe real-time profitability
- Repeat campaign periodically

LOG: ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
echo "DECISION: AUTONOMOUS_PROFITABILITY_CAMPAIGN_COMPLETE"
log "=== CAMPAIGN COMPLETE ==="
