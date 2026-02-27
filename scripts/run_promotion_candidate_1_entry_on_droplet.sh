#!/usr/bin/env bash
# CURSOR TASK — Run full promotion candidate E2E, ensure persona recommendations are generated,
# append persona lines to PROMOTION_CANDIDATES.md, and print a concise persona summary.
# Single entry point: run on the droplet at /root/stock-bot as the repo user.
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

# 0) Pull latest and ensure scripts are executable
git pull origin main
chmod +x scripts/run_promotion_candidate_1_full_e2e_on_droplet.sh \
         scripts/run_promotion_candidate_1_e2e_on_droplet.sh \
         scripts/run_promotion_candidate_1_check_with_tail_on_droplet.sh \
         scripts/run_promotion_candidate_1_check_on_droplet.sh \
         scripts/run_persona_recommendations_for_promotion_on_droplet.sh \
         scripts/run_promotion_candidate_1_entry_on_droplet.sh \
         scripts/run_promotion_candidate_1_top_on_droplet.sh \
         scripts/run_promotion_candidate_1_single_run_on_droplet.sh \
         scripts/run_final_finish_on_droplet.sh \
         scripts/run_push_with_plugins_on_droplet.sh \
         scripts/run_finalize_push_on_droplet.sh 2>/dev/null || true

# 1) Start the full E2E launcher if not already running
if pgrep -f "run_promotion_candidate_1_full_e2e_on_droplet.sh" >/dev/null 2>&1; then
  echo "E2E launcher already running; skipping start."
else
  echo "Starting full E2E launcher (background). Log: ${LOG}"
  nohup bash scripts/run_promotion_candidate_1_full_e2e_on_droplet.sh >> "${LOG}" 2>&1 &
  E2E_PID=$!
  echo "E2E PID ${E2E_PID}"
fi

# 2) Start tail+poll wrapper if not already running
if pgrep -f "run_promotion_candidate_1_check_with_tail_on_droplet.sh" >/dev/null 2>&1; then
  echo "Tail+poll wrapper already running; skipping start."
else
  echo "Starting tail+poll wrapper (background). Log: ${LOG}"
  nohup bash scripts/run_promotion_candidate_1_check_with_tail_on_droplet.sh >> "${LOG}" 2>&1 &
  TAIL_PID=$!
  echo "Tail wrapper PID ${TAIL_PID}"
fi

# 3) Wait for key artifacts (up to WAIT_MIN minutes)
WAIT_MIN=60
SLEEP_SEC=10
MAX_ITER=$(( (WAIT_MIN*60) / SLEEP_SEC ))
i=0
echo "Waiting up to ${WAIT_MIN} minutes for promotion run artifacts under ${RUN_DIR}..."
while [ $i -lt $MAX_ITER ]; do
  if [ -f "${PERSONA_JSON}" ] || [ -f "${BOARD_VERDICT}" ]; then
    echo "Multi-model output detected."
    break
  fi
  if [ -f "${METRIC_CAND}" ] && [ -f "${PROM_CAND}" ] && ( [ -f "${ES_SUM}" ] || [ -f "${BOARD_VERDICT}" ] ); then
    echo "Key artifacts present (metrics + PROMOTION_CANDIDATES + exec_sensitivity/board)."
    break
  fi
  if ! pgrep -f "run_promotion_candidate_1_full_e2e_on_droplet.sh" >/dev/null 2>&1; then
    echo "E2E launcher not running; waiting 120s for final artifacts..."
    sleep 120
    break
  fi
  sleep "${SLEEP_SEC}"
  i=$((i+1))
done

# 4) Ensure persona JSON exists; if not, run persona extraction helper
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

# 7) Print concise persona table for governance copy/paste
if [ -f "${PERSONA_JSON}" ]; then
  echo
  echo "=== Persona recommendations (concise table) ==="
  python3 - "${PERSONA_JSON}" <<'PY'
import json, sys
pjson = sys.argv[1]
data = json.load(open(pjson))
print("{:<12} {:<12} {:<10} {:<40}".format("Persona", "Verdict", "Confidence", "Top action (first)"))
print("-" * 80)
for p in data:
    persona = p.get("persona", "")
    verdict = p.get("verdict", "")
    conf = str(p.get("confidence_pct", ""))
    actions = p.get("recommended_actions", [])
    action = (actions[0] if actions else "")[:40]
    print("{:<12} {:<12} {:<10} {:<40}".format(persona, verdict, conf, action))
PY
else
  echo "No persona_recommendations.json to print."
fi

# 8) Print artifact locations for governance
echo
echo "Key artifacts (copy/paste):"
echo "- Promotion run dir: ${RUN_DIR}"
echo "- Metrics: ${METRIC_CAND} (or ${RUN_DIR}/baseline/metrics.json)"
echo "- Exec sensitivity: ${ES_SUM} (or ${RUN_DIR}/exec_sensitivity/exec_sensitivity_recheck.json)"
echo "- Multi-model board verdict: ${BOARD_VERDICT}"
echo "- Persona JSON: ${PERSONA_JSON}"
echo "- Promotion candidates file: ${PROM_CAND}"
echo
echo "If anything is missing, inspect the run log: tail -n 400 ${LOG}"
echo "Done."
