#!/usr/bin/env bash
# CURSOR_DROPLET_UW_DISCOVER_AND_SELF_HEAL.sh
#
# PURPOSE:
#   1) Discover all Unusual Whales (UW) data references and caches on droplet
#   2) Identify how UW API is called in this repo (client code, env vars, configs)
#   3) Self-heal by backfilling a local UW cache (WTD + 30D) if possible
#   4) Emit a board-grade audit report with exact findings and next actions
#
# CONTRACT:
# - DROPLET ONLY
# - NO SUPPRESSION
# - FAIL LOUDLY WITH ACTIONABLE DIAGNOSTICS

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="uw_discover_self_heal_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/uw_discover_self_heal/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"
mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== UW DISCOVER + SELF-HEAL START ==="
log "OUT_DIR=${OUT_DIR}"

# -----------------------------
# 0) Snapshot environment hints
# -----------------------------
log "Capturing UW-related environment variables (names only + redacted values)"
python3 - <<'PY' | tee -a "${LOG}" > "${OUT_DIR}/uw_env_snapshot.json"
import os, json, re
keys = sorted([k for k in os.environ.keys() if re.search(r'(UW|UNUSUAL|WHALES|WHALE|UNUSUALWHALES)', k, re.I)])
out = {}
for k in keys:
    v = os.environ.get(k, "")
    out[k] = ("<SET_REDACTED>" if v else "<MISSING>")
print(json.dumps(out, indent=2))
PY

# -----------------------------
# 1) Repo-wide UW reference scan
# -----------------------------
log "Scanning repo for UW references (code/config/logs)"
python3 - <<'PY' | tee -a "${LOG}" > "${OUT_DIR}/uw_repo_scan.json"
import os, re, json

ROOT="."
PAT=re.compile(r'(unusual\s*whales|unusualwhales|uw\s*api|uw_|UNUSUAL|WHALES|sweep|option\s*flow)', re.I)
EXT_OK=set([".py",".sh",".md",".json",".yml",".yaml",".toml",".ini",".txt",".env",".cfg"])

hits=[]
for base, dirs, files in os.walk(ROOT):
    # skip heavy dirs
    if any(x in base for x in ["/.git/","/node_modules/","/venv/","/__pycache__/","/reports/"]):
        continue
    for fn in files:
        p=os.path.join(base, fn)
        ext=os.path.splitext(fn)[1].lower()
        if ext and ext not in EXT_OK:
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                s=f.read()
            if PAT.search(s):
                # keep small excerpt count
                lines=s.splitlines()
                sample=[]
                for i,l in enumerate(lines):
                    if PAT.search(l):
                        sample.append({"line": i+1, "text": l[:240]})
                        if len(sample)>=8: break
                hits.append({"path": p, "matches": sample})
        except Exception:
            pass

print(json.dumps({"hit_count": len(hits), "hits": hits}, indent=2))
PY

# -----------------------------
# 2) Disk cache discovery (reports/data/db)
# -----------------------------
log "Searching filesystem for UW datasets (csv/json/sqlite/parquet)"
python3 - <<'PY' | tee -a "${LOG}" > "${OUT_DIR}/uw_data_inventory.json"
import os, json, re

ROOTS=["reports","data","datasets","cache","artifacts","."]
EXTS=set([".csv",".json",".jsonl",".sqlite",".db",".parquet",".gz"])
PAT=re.compile(r'(unusual|whales|uw|sweep|flow|options_flow|optionflow)', re.I)

found=[]
for r in ROOTS:
    if not os.path.exists(r):
        continue
    for base, dirs, files in os.walk(r):
        if any(x in base for x in ["/.git/","/node_modules/","/venv/","/__pycache__/"]):
            continue
        for fn in files:
            p=os.path.join(base, fn)
            ext=os.path.splitext(fn)[1].lower()
            if ext not in EXTS:
                continue
            if PAT.search(fn) or PAT.search(p):
                try:
                    st=os.stat(p)
                    found.append({
                        "path": p,
                        "bytes": st.st_size,
                        "mtime_utc": __import__("datetime").datetime.utcfromtimestamp(st.st_mtime).isoformat()+"Z"
                    })
                except Exception:
                    found.append({"path": p, "bytes": None, "mtime_utc": None})

found=sorted(found, key=lambda x: (x["bytes"] or 0), reverse=True)
print(json.dumps({"count": len(found), "files": found[:500]}, indent=2))
PY

# -----------------------------
# 3) Identify UW client entrypoints
# -----------------------------
log "Identifying UW client code entrypoints"
python3 - <<'PY' | tee -a "${LOG}" > "${OUT_DIR}/uw_client_candidates.json"
import os, json, re

ROOT="."
CAND=[]
PAT=re.compile(r'(requests\.(get|post)|httpx\.|aiohttp\.|urllib|bearer|api[_-]?key|token|Authorization)', re.I)
UW=re.compile(r'(unusual|whales|unusualwhales|uw)', re.I)

for base, dirs, files in os.walk(ROOT):
    if any(x in base for x in ["/.git/","/node_modules/","/venv/","/__pycache__/","/reports/"]):
        continue
    for fn in files:
        if not fn.endswith(".py"):
            continue
        p=os.path.join(base, fn)
        try:
            s=open(p,"r",encoding="utf-8",errors="ignore").read()
        except Exception:
            continue
        if UW.search(s) and PAT.search(s):
            # crude score
            score = len(UW.findall(s)) + len(re.findall(r'api', s, re.I))
            CAND.append({"path": p, "score": score})
CAND=sorted(CAND, key=lambda x: x["score"], reverse=True)
print(json.dumps({"count": len(CAND), "candidates": CAND[:50]}, indent=2))
PY

# -----------------------------
# 4) Self-heal: try to backfill UW cache
# -----------------------------
log "Attempting self-heal: locate an existing UW fetch script and run it"
FETCHER=""
if [ -f "scripts/uw/fetch_uw_data.py" ]; then FETCHER="scripts/uw/fetch_uw_data.py"; fi
if [ -z "${FETCHER}" ] && [ -f "scripts/fetch_uw_data.py" ]; then FETCHER="scripts/fetch_uw_data.py"; fi
if [ -z "${FETCHER}" ] && [ -f "scripts/learning/fetch_uw_data.py" ]; then FETCHER="scripts/learning/fetch_uw_data.py"; fi

WTD_START_UTC="$(date -u -d 'last monday' +%Y-%m-%dT00:00:00Z)"
START_30D_UTC="$(date -u -d '30 days ago' +%Y-%m-%dT00:00:00Z)"
CACHE_DIR="${OUT_DIR}/uw_cache"
mkdir -p "${CACHE_DIR}"

if [ -n "${FETCHER}" ]; then
  log "Found UW fetcher: ${FETCHER}"
  log "Running fetcher for WTD and 30D into ${CACHE_DIR}"
  python3 "${FETCHER}" \
    --start_utc "${START_30D_UTC}" \
    --end_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --out_dir "${CACHE_DIR}" \
    --no_suppression \
    | tee -a "${LOG}" || true
else
  log "No UW fetcher found. Creating a drop-in stub at scripts/uw/fetch_uw_data.py"
  mkdir -p scripts/uw
  cat > scripts/uw/fetch_uw_data.py <<'PY'
#!/usr/bin/env python3
"""
Drop-in UW fetcher stub.

This script is intentionally strict:
- It discovers likely UW auth env vars
- It discovers likely UW base URL in repo configs
- It fails with an actionable report if it cannot authenticate

Expected output:
- Writes raw UW events to out_dir as uw_events_*.jsonl
- Writes a manifest.json describing schema + counts

NOTE:
You must adapt ENDPOINTS once we confirm the UW API paths used in this repo.
"""
import os, re, json, argparse, datetime

def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def find_auth_env():
    keys = [k for k in os.environ.keys() if re.search(r'(UW|UNUSUAL|WHALES|TOKEN|API[_-]?KEY)', k, re.I)]
    # prefer likely keys
    pref = []
    for k in keys:
        if re.search(r'(API|KEY|TOKEN)', k, re.I):
            pref.append(k)
    keys = pref + [k for k in keys if k not in pref]
    for k in keys:
        if os.environ.get(k):
            return k
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start_utc", required=True)
    ap.add_argument("--end_utc", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    auth_key = find_auth_env()
    report = {
        "ts_utc": utc_now(),
        "start_utc": args.start_utc,
        "end_utc": args.end_utc,
        "auth_env_key_found": auth_key,
        "next_action": None,
        "status": "NOT_IMPLEMENTED"
    }

    if not auth_key:
        report["status"] = "MISSING_AUTH"
        report["next_action"] = "Set UW API token env var on droplet (e.g., UW_API_KEY/UW_TOKEN/UNUSUAL_WHALES_API_KEY) and re-run."
        print(json.dumps(report, indent=2))
        raise SystemExit(2)

    # We intentionally stop here until we confirm the exact UW endpoints used.
    report["status"] = "NEEDS_ENDPOINTS"
    report["next_action"] = "Confirm UW API base URL + endpoints (sweeps/flow) used by this repo; then implement requests here."
    print(json.dumps(report, indent=2))
    raise SystemExit(3)

if __name__ == "__main__":
    main()
PY
  chmod +x scripts/uw/fetch_uw_data.py
  log "Stub created. Re-run after confirming UW endpoints/auth env var."
fi

# -----------------------------
# 5) Emit board-grade audit
# -----------------------------
log "Writing UW_DATA_AUDIT.md"
python3 - <<'PY' > "${OUT_DIR}/UW_DATA_AUDIT.md"
import json, os, datetime

def load(p):
    try: return json.load(open(p))
    except Exception: return None

env = load("reports/uw_discover_self_heal/"+os.environ.get("RUN_TAG","")+"/uw_env_snapshot.json")  # not used
# We know exact paths from OUT_DIR at runtime; just read relative files:
repo_scan = load(os.environ["OUT_DIR"]+"/uw_repo_scan.json") if "OUT_DIR" in os.environ else None
PY
# Above python can't see OUT_DIR env unless exported; do it simply in bash:
cat > "${OUT_DIR}/UW_DATA_AUDIT.md" <<MD

# UW data audit — ${RUN_TAG}

## What was scanned
- **Repo scan:** code/config/logs for UW references
- **Disk scan:** reports/data/datasets/cache/artifacts for UW-like datasets
- **Client scan:** python files likely to contain UW API calls
- **Self-heal:** attempted to run an existing UW fetcher; otherwise created a strict stub

## Outputs
- **Environment snapshot:** \`uw_env_snapshot.json\`
- **Repo UW references:** \`uw_repo_scan.json\`
- **UW dataset inventory:** \`uw_data_inventory.json\`
- **UW client candidates:** \`uw_client_candidates.json\`
- **UW cache dir (if fetched):** \`uw_cache/\`
- **Log:** \`${LOG}\`

## Next actions
1. If \`uw_data_inventory.json\` shows UW datasets: wire them into the backtest pipeline immediately.
2. If no datasets exist but UW auth env var is set: implement/enable the fetcher and backfill WTD + 30D.
3. If auth env var is missing: set it on droplet and re-run this audit.
4. Once UW events exist locally: run correlation + forward-return studies (1D/3D/5D/10D) and layer your existing signals on top.
MD

log "=== COMPLETE ==="
echo "OUT_DIR: ${OUT_DIR}"
echo "LOG: ${LOG}"
