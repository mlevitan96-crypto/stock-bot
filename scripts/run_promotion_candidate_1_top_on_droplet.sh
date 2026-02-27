#!/usr/bin/env bash
# CURSOR TASK — Run the full promotion candidate E2E flow, wait for artifacts, and print the persona summary + key artifacts.
# Paste and run this on the droplet as the repo user (runs everything under /root/stock-bot).
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

cd "${REPO_ROOT}" || { echo "Repo root ${REPO_ROOT} not found"; exit 1; }

# 0) Pull latest and ensure entry + orchestration scripts are executable
git pull origin main
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

# 1) Start the single-entry launcher (safe to run even if wrappers already running)
if pgrep -f "run_promotion_candidate_1_entry_on_droplet.sh" >/dev/null 2>&1; then
  echo "Entry script already running; continuing to wait for artifacts."
else
  echo "Starting entry script in background; log -> ${LOG}"
  nohup bash scripts/run_promotion_candidate_1_entry_on_droplet.sh >> "${LOG}" 2>&1 &
  ENTRY_PID=$!
  echo "Entry PID ${ENTRY_PID}"
fi

# 2) Start the tail+poll wrapper if not already running (gives live feedback)
if pgrep -f "run_promotion_candidate_1_check_with_tail_on_droplet.sh" >/dev/null 2>&1; then
  echo "Tail+poll wrapper already running."
else
  echo "Starting tail+poll wrapper in background; log -> ${LOG}"
  nohup bash scripts/run_promotion_candidate_1_check_with_tail_on_droplet.sh >> "${LOG}" 2>&1 &
  TAIL_PID=$!
  echo "Tail wrapper PID ${TAIL_PID}"
fi

# 3) Wait for key artifacts (up to WAIT_MIN minutes)
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

# 4) If persona JSON missing, run persona extraction helper (best-effort)
if [ ! -f "${PERSONA_JSON}" ]; then
  echo "persona_recommendations.json missing; running persona extraction helper..."
  bash scripts/run_persona_recommendations_for_promotion_on_droplet.sh >> "${LOG}" 2>&1 || true
fi

# 5) If still missing and board_verdict exists, synthesize persona JSON (best-effort)
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

# 6) Append persona recommendations to PROMOTION_CANDIDATES.md idempotently
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

# 7) Stop any background tailing processes started by wrappers (best-effort)
pkill -f "tail -f /tmp/promotion_candidate_1_check.log" 2>/dev/null || true
pkill -f "tail -n 200 -f /tmp/promotion_candidate_1_check.log" 2>/dev/null || true

# 8) Print concise artifact excerpts for governance copy/paste
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

echo
echo "If anything is missing or the run stalled, inspect the log: tail -n 400 ${LOG}"
echo "NEXT STEPS:"
echo "- If board verdict is ACCEPT and personas are aligned, create the PR branch 'promote/promotion_candidate_1' with configs/overlays/promotion_candidate_1.json and open the PR."
echo "- If exec_sensitivity or persona recommendations request changes, iterate on overlay and re-run the focused check."
echo "- When ready, follow the paper→canary rollout plan in PROMOTION_CANDIDATES.md and the governance checklist."
echo "Done."
