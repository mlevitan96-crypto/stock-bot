#!/usr/bin/env bash
# CURSOR_ONE_BLOCK_DEPLOY_AND_VERIFY_SIGNALS.sh
# Goal: Deploy fixes (FTD/calendar normalization + shorts component logic), restart services,
# re-run audits, and produce a final evidence report proving whether trading can resume.
# Droplet only: /root/stock-bot
set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
LOG="/tmp/cursor_deploy_verify_signals.log"
RUN_TAG="deploy_verify_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/backtests/signal_fix_verification_${RUN_TAG}"
EXCERPTS="/tmp/signal_fix_excerpts_${RUN_TAG}"

MIN_EXEC_SCORE="${MIN_EXEC_SCORE:-2.5}"
DAYS="${DAYS:-7}"

mkdir -p "${RUN_DIR}" "${EXCERPTS}"
: >> "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found at ${REPO}"

log "=== START deploy+verify (${RUN_TAG}) ==="
log "Repo: ${REPO}"
log "Run dir: ${RUN_DIR}"
log "Log: ${LOG}"

# ----------------------------
# 1) Update code on droplet
# ----------------------------
log "Updating repo to latest origin/main"
git fetch origin main >> "${LOG}" 2>&1
git reset --hard origin/main >> "${LOG}" 2>&1
git status --porcelain | tee -a "${LOG}" || true

# Sanity: ensure the expected files exist (fail fast if not)
test -f uw_flow_daemon.py || fail "uw_flow_daemon.py missing"
test -f uw_composite_v2.py || fail "uw_composite_v2.py missing"
test -f reports/signal_review/SIGNAL_ZERO_ROOT_CAUSE_AND_FIXES.md || log "Note: SIGNAL_ZERO_ROOT_CAUSE_AND_FIXES.md not found (non-fatal)"

# ----------------------------
# 2) Restart services via systemd (droplet standard)
# ----------------------------
log "Restarting services via systemd (stock-bot, uw-flow-daemon)"
sudo systemctl restart uw-flow-daemon.service >> "${LOG}" 2>&1 || log "uw-flow-daemon restart failed (non-fatal)"
sudo systemctl restart stock-bot.service >> "${LOG}" 2>&1 || log "stock-bot restart failed (non-fatal)"
sleep 10
log "Process snapshot:"
ps aux | grep -E 'uw_flow_daemon|stock-bot|main.py|deploy_supervisor' | grep -v grep | head -n 30 | tee -a "${LOG}" || true

# ----------------------------
# 3) Validate UW cache freshness + normalized shapes
# ----------------------------
UW_CACHE="data/uw_flow_cache.json"
log "Validating UW cache: ${UW_CACHE}"
test -f "${UW_CACHE}" || fail "UW cache missing: ${UW_CACHE}"

# Cache is a dict: symbol -> data (not a list)
CACHE_COUNT=$(python3 - <<PY
import json
p = "${UW_CACHE}"
d = json.load(open(p))
if isinstance(d, dict):
    # Skip metadata keys
    syms = [k for k in d if isinstance(k, str) and not k.startswith("_")]
    print(len(syms))
else:
    print(0)
PY
)
log "UW cache symbol count: ${CACHE_COUNT}"
[ "${CACHE_COUNT}" -ge 10 ] || fail "UW cache too small (<10 symbols). Daemon may not be populating."

CACHE_MTIME=$(stat -c %Y "${UW_CACHE}")
NOW=$(date +%s)
AGE=$((NOW - CACHE_MTIME))
log "UW cache age seconds: ${AGE}"
[ "${AGE}" -le 7200 ] || log "WARNING: UW cache may be stale (>7200s). Daemon may still be warming."

# Check for normalized keys in a sample (cache is dict symbol -> data)
log "Checking for normalized shapes in cache (ftd_pressure / calendar)"
python3 - <<'PY' | tee "${EXCERPTS}/cache_shape_check.txt" | tee -a "${LOG}"
import json
p = "data/uw_flow_cache.json"
d = json.load(open(p))
if isinstance(d, dict):
    sample = [v for k, v in list(d.items())[:200] if isinstance(v, dict) and not str(k).startswith("_")]
else:
    sample = []
def has_norm_ftd(rec):
    x = rec.get("ftd_pressure") or rec.get("shorts_ftds") or {}
    return isinstance(x, dict) and any(k in x for k in ["ftd_count", "squeeze_risk", "interest_pct", "days_to_cover"])
def has_norm_cal(rec):
    x = rec.get("calendar") or {}
    return isinstance(x, dict) and any(k in x for k in ["has_earnings", "days_to_earnings", "has_fda", "economic_events"])
ftd = sum(1 for r in sample if has_norm_ftd(r))
cal = sum(1 for r in sample if has_norm_cal(r))
print({"sample": len(sample), "ftd_normalized": ftd, "calendar_normalized": cal})
PY

# ----------------------------
# 4) Run scoring pipeline audit (produces funnel + audit report)
# ----------------------------
log "Running scoring pipeline trade-blocker audit (last ${DAYS} days)"
python3 scripts/run_scoring_pipeline_audit_on_droplet.py --days "${DAYS}" 2>&1 | tee "${EXCERPTS}/scoring_audit_raw.log" | tee -a "${LOG}" || true

# Copy audit outputs from reports/signal_review (actual audit output location)
SIGNAL_REVIEW="${REPO}/reports/signal_review"
for f in SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md signal_funnel.json signal_audit_diagnostic_droplet.json; do
  if [ -f "${SIGNAL_REVIEW}/${f}" ]; then
    cp "${SIGNAL_REVIEW}/${f}" "${EXCERPTS}/" || true
  fi
done
if [ -f "${SIGNAL_REVIEW}/signal_funnel.json" ]; then
  cp "${SIGNAL_REVIEW}/signal_funnel.json" "${RUN_DIR}/signal_funnel.json" || true
fi

# ----------------------------
# 5) Score stats from funnel (primary) or from breakdown log if present
# ----------------------------
log "Computing score stats and % above MIN_EXEC_SCORE=${MIN_EXEC_SCORE}"
python3 - <<PY > "${RUN_DIR}/score_stats.json"
import json, os, statistics

min_exec = float("${MIN_EXEC_SCORE}")
run_dir = "${RUN_DIR}"
excerpts = "${EXCERPTS}"

# Prefer funnel (from audit) for total_candidates and pct_above_min_exec_post
funnel_path = os.path.join(run_dir, "signal_funnel.json")
if not os.path.exists(funnel_path):
    funnel_path = os.path.join(excerpts, "signal_funnel.json")

out = {"count": 0, "above_min_exec": 0, "frac_above_min_exec": 0.0, "median": None, "mean": None, "min": None, "max": None, "source": "none"}

if os.path.exists(funnel_path):
    try:
        with open(funnel_path) as f:
            funnel = json.load(f)
        exp = funnel.get("expectancy_distributions") or {}
        post = exp.get("post_adjust") or {}
        total = int(funnel.get("total_candidates", 0))
        pct_above = float(exp.get("pct_above_min_exec_post", 0) or 0)
        above = int(round(total * pct_above / 100.0)) if total else 0
        out["count"] = total
        out["above_min_exec"] = above
        out["frac_above_min_exec"] = (above / total) if total else 0.0
        out["median"] = post.get("p50")
        out["mean"] = post.get("mean")
        out["min"] = post.get("p10")
        out["max"] = post.get("p90")
        out["source"] = "signal_funnel"
    except Exception as e:
        out["error"] = str(e)

# If we have breakdown log, enrich with actual score distribution
breakdown_path = "logs/signal_score_breakdown.jsonl"
if os.path.exists(breakdown_path):
    vals = []
    try:
        for line in open(breakdown_path):
            try:
                o = json.loads(line)
            except Exception:
                continue
            v = o.get("composite_exec_score")
            if v is None:
                v = o.get("score_final") or o.get("composite_score")
            if v is not None:
                try:
                    vals.append(float(v))
                except (TypeError, ValueError):
                    pass
    except Exception:
        pass
    if vals:
        out["count_breakdown"] = len(vals)
        out["median"] = statistics.median(vals)
        out["mean"] = statistics.mean(vals)
        out["min"] = min(vals)
        out["max"] = max(vals)
        out["above_min_exec"] = sum(1 for v in vals if v >= min_exec)
        out["frac_above_min_exec"] = out["above_min_exec"] / len(vals)
        out["source"] = "signal_score_breakdown"

print(json.dumps(out, indent=2))
PY

SCORE_STATS="$(cat "${RUN_DIR}/score_stats.json" 2>/dev/null || echo '{}')"
ABOVE=$(python3 -c "
import json, os
p = '${RUN_DIR}/score_stats.json'
try:
    o = json.load(open(p))
    print(int(o.get('above_min_exec', 0)))
except Exception:
    print(0)
" 2>/dev/null || echo "0")

# ----------------------------
# 6) Multi-model adversarial review (optional)
# ----------------------------
log "Running multi-model adversarial review if runner exists"
if [ -f scripts/multi_model_runner.py ]; then
  mkdir -p "${RUN_DIR}/multi_model_out"
  python3 scripts/multi_model_runner.py \
    --roles prosecutor,defender,board,customer_advocate \
    --evidence "${EXCERPTS}" \
    --out "${RUN_DIR}/multi_model_out" >> "${LOG}" 2>&1 || true
else
  log "multi_model_runner.py not found; skipping"
fi

# ----------------------------
# 7) Final decision + report
# ----------------------------
DECISION="REJECT"
PRIMARY_REASON="No candidates above MIN_EXEC_SCORE after fixes"
if [ "${ABOVE:-0}" -gt 0 ]; then
  DECISION="ALLOW_TRADING"
  PRIMARY_REASON="Candidates now exceed MIN_EXEC_SCORE; expectancy gate should no longer block 100%"
fi

cat > "${RUN_DIR}/cursor_final_summary.txt" <<EOF
RUN_DIR: ${RUN_DIR}
DECISION: ${DECISION}
PRIMARY_REASON: ${PRIMARY_REASON}
MIN_EXEC_SCORE: ${MIN_EXEC_SCORE}
SCORE_STATS_JSON: ${RUN_DIR}/score_stats.json
EXCERPTS_DIR: ${EXCERPTS}
LOG: ${LOG}
EOF

cat > "${RUN_DIR}/cursor_report.md" <<EOF
# Signal Fix Deployment Verification Report

**Generated (droplet):** $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Run dir:** ${RUN_DIR}
**Decision:** ${DECISION}

## What changed (expected)
- FTD/shorts normalization written by daemon into composite-expected shape.
- Calendar normalization written by daemon into composite-expected shape.
- Shorts component no longer returns 0 when interest_pct == 0; can contribute from ftd_count/squeeze_risk.

## Cache validation
- UW cache: ${UW_CACHE}
- Symbol count: ${CACHE_COUNT}
- Age seconds: ${AGE}
- Shape check: $(cat "${EXCERPTS}/cache_shape_check.txt" 2>/dev/null || echo "missing")

## Score distribution (post-fix)
\`\`\`json
${SCORE_STATS}
\`\`\`

## Audit outputs
- Raw audit log: ${EXCERPTS}/scoring_audit_raw.log
- Funnel: ${EXCERPTS}/signal_funnel.json
- Audit report: ${EXCERPTS}/SCORING_PIPELINE_TRADE_BLOCKER_AUDIT.md

## Next step
- If **ALLOW_TRADING**: resume paper/live trading and monitor expectancy gate + signal_health.jsonl.
- If **REJECT**: check daemon logs and cache for normalized keys; ensure UW API returns data for FTD/calendar.
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: ${DECISION}"
log "=== COMPLETE (${DECISION}) ==="
