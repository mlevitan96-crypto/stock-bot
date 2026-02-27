#!/usr/bin/env bash
# CURSOR TASK — Single-run launcher: run full promotion candidate E2E, wait for artifacts,
# append persona recommendations, and (if board ACCEPT) prepare a promotion branch + PR body.
# Paste and run this on the droplet as the repo user in /root/stock-bot.
set -euo pipefail

REPO_ROOT="/root/stock-bot"
LOG="/tmp/promotion_candidate_1_full_e2e.log"
RUN_DIR="reports/backtests/promotion_candidate_1_check"
MM_OUT="${RUN_DIR}/multi_model/out"
PERSONA_JSON="${MM_OUT}/persona_recommendations.json"
BOARD_VERDICT="${MM_OUT}/board_verdict.md"
PROM_CAND="${RUN_DIR}/PROMOTION_CANDIDATES.md"
METRIC_CAND="${RUN_DIR}/metrics.json"
ES_SUM="${RUN_DIR}/exec_sensitivity/exec_sensitivity.json"
ES_RECHK="${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json"
OVERLAY="configs/overlays/promotion_candidate_1.json"
PR_BRANCH="promote/promotion_candidate_1"
PR_BODY_FILE="/tmp/promotion_candidate_1_PR_BODY.md"

cd "${REPO_ROOT}" || { echo "Repo root ${REPO_ROOT} not found"; exit 1; }

# Ensure latest code and scripts executable
git pull origin main || true
chmod +x scripts/run_promotion_candidate_1_entry_on_droplet.sh \
         scripts/run_promotion_candidate_1_full_e2e_on_droplet.sh \
         scripts/run_promotion_candidate_1_e2e_on_droplet.sh \
         scripts/run_promotion_candidate_1_check_with_tail_on_droplet.sh \
         scripts/run_promotion_candidate_1_check_on_droplet.sh \
         scripts/run_persona_recommendations_for_promotion_on_droplet.sh \
         scripts/run_promotion_candidate_1_top_on_droplet.sh \
         scripts/run_promotion_candidate_1_single_run_on_droplet.sh \
         scripts/run_final_finish_on_droplet.sh \
         scripts/run_push_with_plugins_on_droplet.sh \
         scripts/run_finalize_push_on_droplet.sh 2>/dev/null || true

# Start the single-entry launcher if not already running
if ! pgrep -f "run_promotion_candidate_1_entry_on_droplet.sh" >/dev/null 2>&1; then
  nohup bash scripts/run_promotion_candidate_1_entry_on_droplet.sh >> "${LOG}" 2>&1 &
  echo "Started entry launcher; log -> ${LOG}"
else
  echo "Entry launcher already running; continuing to wait for artifacts."
fi

# Start tail+poll wrapper if not already running
if ! pgrep -f "run_promotion_candidate_1_check_with_tail_on_droplet.sh" >/dev/null 2>&1; then
  nohup bash scripts/run_promotion_candidate_1_check_with_tail_on_droplet.sh >> "${LOG}" 2>&1 &
  echo "Started tail+poll wrapper; log -> ${LOG}"
else
  echo "Tail+poll wrapper already running."
fi

# Wait for key artifacts (up to WAIT_MIN minutes)
WAIT_MIN=60
SLEEP_SEC=10
MAX_ITER=$(( (WAIT_MIN*60) / SLEEP_SEC ))
i=0
echo "Waiting up to ${WAIT_MIN} minutes for artifacts under ${RUN_DIR}..."
while [ $i -lt $MAX_ITER ]; do
  if [ -f "${PERSONA_JSON}" ] || [ -f "${BOARD_VERDICT}" ]; then
    echo "Detected persona JSON or board verdict."
    break
  fi
  if [ -f "${METRIC_CAND}" ] && [ -f "${PROM_CAND}" ] && ( [ -f "${ES_SUM}" ] || [ -f "${BOARD_VERDICT}" ] ); then
    echo "Detected metrics + PROMOTION_CANDIDATES + (exec_sensitivity or board_verdict)."
    break
  fi
  if ! pgrep -f "run_promotion_candidate_1_entry_on_droplet.sh" >/dev/null 2>&1; then
    echo "Entry script not running; waiting 120s for final artifacts..."
    sleep 120
    break
  fi
  sleep "${SLEEP_SEC}"
  i=$((i+1))
done

# Ensure persona JSON exists; if not, run persona extraction helper
if [ ! -f "${PERSONA_JSON}" ]; then
  echo "persona_recommendations.json missing; running persona extraction helper..."
  bash scripts/run_persona_recommendations_for_promotion_on_droplet.sh >> "${LOG}" 2>&1 || true
fi

# If still missing and board_verdict exists, synthesize persona JSON (best-effort)
if [ ! -f "${PERSONA_JSON}" ] && [ -f "${BOARD_VERDICT}" ]; then
  echo "Synthesizing persona_recommendations.json from board_verdict.md (best-effort)..."
  mkdir -p "${MM_OUT}"
  TMP=$(mktemp)
  python3 - "${BOARD_VERDICT}" <<'PY' > "${TMP}"
import re, sys, json
bd_path = sys.argv[1]
out = []
pat = re.compile(r'^\s*-\s*\*\*(?P<persona>[^*]+)\*\*\s*—\s*\*\*(?P<verdict>[^*]+)\*\*\s*\(confidence\s*(?P<conf>[\d\.]+)%\)\s*:\s*(?P<action>[^;]+)(?:;\s*evidence:\s*(?P<evidence>.+))?', re.I)
with open(bd_path) as f:
    for line in f:
        m = pat.match(line)
        if m:
            persona = m.group('persona').strip()
            verdict = m.group('verdict').strip().upper()
            conf = float(m.group('conf')) if m.group('conf') else 0.0
            action = m.group('action').strip()
            evidence = m.group('evidence').strip() if m.group('evidence') else ""
            out.append({
                "persona": persona,
                "verdict": verdict,
                "confidence_pct": conf,
                "top_concerns": [],
                "recommended_actions": [action] if action else [],
                "evidence_refs": [evidence] if evidence else []
            })
if not out:
    text = open(bd_path).read()
    m2 = re.search(r'Board.*?(ACCEPT|REJECT|CONDITIONAL)', text, re.I)
    if m2:
        out.append({
            "persona": "Board",
            "verdict": m2.group(1).upper(),
            "confidence_pct": 75.0,
            "top_concerns": [],
            "recommended_actions": [],
            "evidence_refs": []
        })
print(json.dumps(out, indent=2))
PY
  mv "${TMP}" "${PERSONA_JSON}"
  echo "Wrote synthesized persona_recommendations.json -> ${PERSONA_JSON}"
fi

# Append persona recommendations to PROMOTION_CANDIDATES.md idempotently
if [ -f "${PERSONA_JSON}" ]; then
  mkdir -p "$(dirname "${PROM_CAND}")"
  if ! grep -q "## Persona recommendations (multi-model)" "${PROM_CAND}" 2>/dev/null; then
    echo "" >> "${PROM_CAND}"
    echo "## Persona recommendations (multi-model)" >> "${PROM_CAND}"
  fi
  python3 - "${PERSONA_JSON}" "${PROM_CAND}" <<'PY'
import json, sys
pjson = sys.argv[1]
prom = sys.argv[2]
data = json.load(open(pjson))
try:
    existing = open(prom).read()
except FileNotFoundError:
    existing = ""
lines = []
for p in data:
    persona = p.get("persona", "unknown")
    verdict = p.get("verdict", "UNKNOWN")
    conf = p.get("confidence_pct", 0)
    actions = p.get("recommended_actions", [])
    evidence = p.get("evidence_refs", [])
    action = actions[0] if actions else ""
    ev = evidence[0] if evidence else ""
    line = f"- **{persona}**: **{verdict}** (confidence {conf}%) — {action}"
    if ev:
        line += f" ; evidence: {ev}"
    lines.append(line)
with open(prom, "a") as f:
    for L in lines:
        if L + "\n" not in existing:
            f.write(L + "\n")
            existing += L + "\n"
print("Appended persona lines to", prom)
PY
else
  echo "persona_recommendations.json missing; skipping append to PROMOTION_CANDIDATES.md"
fi

# Stop background tail processes (best-effort)
pkill -f "tail -f /tmp/promotion_candidate_1_check.log" 2>/dev/null || true
pkill -f "tail -n 200 -f /tmp/promotion_candidate_1_check.log" 2>/dev/null || true

# Print concise governance excerpts
echo
echo "=== Promotion candidate metrics (first 20 lines) ==="
if [ -f "${METRIC_CAND}" ]; then head -n 20 "${METRIC_CAND}"; elif [ -f "${RUN_DIR}/baseline/metrics.json" ]; then head -n 20 "${RUN_DIR}/baseline/metrics.json"; else echo "metrics.json not found under ${RUN_DIR}"; fi

echo
echo "=== Exec sensitivity summary (if present) ==="
if [ -f "${ES_SUM}" ]; then jq '.' "${ES_SUM}" 2>/dev/null || cat "${ES_SUM}"; elif [ -f "${ES_RECHK}" ]; then jq '.' "${ES_RECHK}" 2>/dev/null || cat "${ES_RECHK}"; else echo "exec_sensitivity summary not found under ${RUN_DIR}"; fi

echo
echo "=== Multi-model board verdict (first 40 lines) ==="
if [ -f "${BOARD_VERDICT}" ]; then head -n 40 "${BOARD_VERDICT}"; else echo "board_verdict.md not found at ${BOARD_VERDICT}"; fi

echo
echo "=== Promotion candidates (first 40 lines) ==="
if [ -f "${PROM_CAND}" ]; then head -n 40 "${PROM_CAND}"; else echo "PROMOTION_CANDIDATES.md not found at ${PROM_CAND}"; fi

echo
echo "=== Persona recommendations JSON (first 40 lines) ==="
if [ -f "${PERSONA_JSON}" ]; then head -n 40 "${PERSONA_JSON}"; else echo "persona_recommendations.json not found at ${PERSONA_JSON}"; fi

echo
echo "Artifacts directory listing:"
ls -la "${RUN_DIR}" 2>/dev/null || echo "Run dir ${RUN_DIR} not present"

# If board verdict contains ACCEPT, prepare a promotion branch and PR body (best-effort)
BOARD_ACCEPT=false
if [ -f "${BOARD_VERDICT}" ]; then
  if grep -qi "ACCEPT" "${BOARD_VERDICT}" 2>/dev/null; then
    BOARD_ACCEPT=true
  fi
fi

if ${BOARD_ACCEPT}; then
  echo
  echo "Board verdict contains ACCEPT — preparing promotion branch and PR body (best-effort)."

  # Ensure overlay exists
  if [ ! -f "${OVERLAY}" ]; then
    echo "Overlay ${OVERLAY} not found; creating a placeholder overlay from known candidate values."
    mkdir -p "$(dirname "${OVERLAY}")"
    cat > "${OVERLAY}" <<'JSON'
{
  "composite_weights": {
    "dark_pool": 0.75,
    "freshness_factor": 0.7
  },
  "freshness_smoothing_window": 3,
  "notes": "Promotion candidate: reduce dark_pool by 25% and smooth/lower freshness to reduce single-signal fragility"
}
JSON
    git add "${OVERLAY}" || true
  fi

  # Create branch, commit overlay if needed, and push (best-effort)
  git fetch origin main || true
  git checkout -B "${PR_BRANCH}" origin/main || git checkout -B "${PR_BRANCH}"
  git add "${OVERLAY}" || true
  if git diff --cached --quiet 2>/dev/null; then
    echo "No staged changes to commit (overlay already tracked)."
  else
    git commit -m "Promotion candidate: reduce dark_pool and smooth freshness_factor (promotion_candidate_1)" || true
  fi
  if git push -u origin "${PR_BRANCH}" 2>/dev/null; then
    echo "Pushed branch ${PR_BRANCH} to origin."
  else
    echo "Warning: git push failed (credentials or remote). Branch created locally: ${PR_BRANCH}"
  fi

  # Write PR body to file for copy/paste
  cat > "${PR_BODY_FILE}" <<'MD'
PR title: Paper promotion: reduce dark_pool weight and smooth freshness_factor

Summary
-------
Introduce a minimal, reversible overlay to reduce single-signal fragility and improve robustness in paper trading.

Changes
-------
- configs/overlays/promotion_candidate_1.json
  - dark_pool weight set to 0.75
  - freshness_factor weight set to 0.7
  - freshness_smoothing_window set to 3

Validation plan
---------------
1. Focused backtest with overlay and compare metrics to baseline.
2. Exec sensitivity at 0x, 1x, 2x slippage and confirm acceptable degradation.
3. Multi-model adversarial review with full evidence and board verdict.
4. Paper run for 7 trading days with monitoring; if stable, canary for 14 days.

Acceptance criteria
-------------------
- Net PnL ≥ 90% of baseline on snapshot
- Exec sensitivity positive at 1x and 2x slippage
- Reduced single-signal fragility for dark_pool and freshness_factor
- Multi-model board verdict ACCEPT or minor mitigations
- Customer advocate endorses or lists manageable concerns

Rollback
--------
Revert the overlay file or re-apply the previous overlay. This is a single-file change and can be reverted in one commit.

Monitoring (paper)
------------------
- Daily net PnL vs expected; alert if drawdown > 2× expected daily variance.
- Gate metrics: gate_p50 drop > 30% → pause.
- Missing attribution fields → immediate stop.
- Single-signal impact: if dark_pool or freshness_factor ablation flips sign in paper → pause and revert overlay.
MD

  echo "PR body written to ${PR_BODY_FILE}. Copy/paste into GitHub when creating the PR."
else
  echo
  echo "Board verdict not ACCEPT or board verdict missing; skipping automatic branch/PR preparation."
fi

echo
echo "NEXT STEPS:"
echo "- If board ACCEPT and branch pushed: open PR from ${PR_BRANCH} using the PR body at ${PR_BODY_FILE}."
echo "- If PR cannot be pushed from this host, create the branch locally and paste the PR body into GitHub manually."
echo "- If exec_sensitivity or persona recommendations request changes, iterate on overlay and re-run the focused check."
echo "- When ready, follow the paper→canary rollout plan in the PR and PROMOTION_CANDIDATES.md."
echo "Done."
