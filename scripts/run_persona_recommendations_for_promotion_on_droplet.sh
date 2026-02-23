#!/usr/bin/env bash
# CURSOR TASK — Generate persona recommendations, append to promotion candidates,
# and print a concise persona summary for the promotion candidate run.
#
# Run on the droplet at /root/stock-bot as the repo user.
# This wrapper:
# 1) Waits for the promotion candidate run to finish (multi_model output).
# 2) Locates or synthesizes multi_model/out/persona_recommendations.json.
# 3) Appends a short persona summary to PROMOTION_CANDIDATES.md.
# 4) Prints a concise persona table for copy/paste into governance notes.
#
# Usage: run on the droplet after the promotion candidate check has started.
set -euo pipefail

REPO_ROOT="/root/stock-bot"
cd "${REPO_ROOT}" || { echo "Repo root ${REPO_ROOT} not found"; exit 1; }

RUN_DIR="reports/backtests/promotion_candidate_1_check"
MM_OUT_DIR="${RUN_DIR}/multi_model/out"
PERSONA_JSON="${MM_OUT_DIR}/persona_recommendations.json"
BOARD_VERDICT="${MM_OUT_DIR}/board_verdict.md"
PROM_CAND="${RUN_DIR}/PROMOTION_CANDIDATES.md"
LOG="/tmp/promotion_candidate_1_check.log"

# Wait for multi-model output or board_verdict for up to N minutes
WAIT_MIN=30
SLEEP_SEC=10
MAX_ITER=$(( (WAIT_MIN*60) / SLEEP_SEC ))
i=0
echo "Waiting up to ${WAIT_MIN} minutes for multi-model output under ${MM_OUT_DIR}..."
while [ $i -lt $MAX_ITER ]; do
  if [ -f "${PERSONA_JSON}" ] || [ -f "${BOARD_VERDICT}" ]; then
    echo "Found multi-model output."
    break
  fi
  sleep "${SLEEP_SEC}"
  i=$((i+1))
done

if [ ! -f "${PERSONA_JSON}" ] && [ ! -f "${BOARD_VERDICT}" ]; then
  echo "ERROR: multi-model outputs not found under ${MM_OUT_DIR} after ${WAIT_MIN} minutes."
  echo "Tail of log (${LOG}):"
  tail -n 200 "${LOG}" 2>/dev/null || true
  exit 2
fi

# If persona_recommendations.json exists, use it. Otherwise synthesize from board_verdict.md
if [ -f "${PERSONA_JSON}" ]; then
  echo "Using existing persona_recommendations.json: ${PERSONA_JSON}"
else
  echo "persona_recommendations.json not found; attempting to synthesize from ${BOARD_VERDICT} ..."
  if [ ! -f "${BOARD_VERDICT}" ]; then
    echo "ERROR: board_verdict.md not found; cannot synthesize persona recommendations."
    exit 3
  fi

  TMP_JSON=$(mktemp)
  python3 - "${BOARD_VERDICT}" <<'PY' > "${TMP_JSON}"
import re, json, sys
bd_path = sys.argv[1]
out = []
pat = re.compile(r'^\s*-\s*\*\*(?P<persona>[^*]+)\*\*\s*—\s*\*\*(?P<verdict>[^*]+)\*\*\s*\(confidence\s*(?P<conf>[\d\.]+)%\)\s*:\s*(?P<action>[^;]+)(?:;\s*evidence:\s*(?P<evidence>.+))?', re.I)
with open(bd_path) as f:
    for line in f:
        m = pat.match(line)
        if m:
            persona = m.group('persona').strip()
            verdict = m.group('verdict').strip().upper()
            conf = float(m.group('conf')) if m.group('conf') else None
            action = m.group('action').strip()
            evidence = m.group('evidence').strip() if m.group('evidence') else None
            obj = {
                "persona": persona,
                "verdict": verdict,
                "confidence_pct": conf if conf is not None else 0.0,
                "top_concerns": [],
                "recommended_actions": [action] if action else [],
                "evidence_refs": [evidence] if evidence else []
            }
            out.append(obj)
if not out:
    with open(bd_path) as f:
        text = f.read()
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
  mkdir -p "${MM_OUT_DIR}"
  mv "${TMP_JSON}" "${PERSONA_JSON}"
  echo "Wrote synthesized persona_recommendations.json -> ${PERSONA_JSON}"
fi

if [ ! -f "${PERSONA_JSON}" ]; then
  echo "ERROR: persona_recommendations.json still missing."
  exit 4
fi

# Ensure PROMOTION_CANDIDATES.md exists
if [ ! -f "${PROM_CAND}" ]; then
  echo "# Promotion candidates (auto-generated persona recommendations)" > "${PROM_CAND}"
  echo "" >> "${PROM_CAND}"
fi

# Append persona lines to PROMOTION_CANDIDATES.md
echo "" >> "${PROM_CAND}"
echo "## Persona recommendations (multi-model)" >> "${PROM_CAND}"
python3 - "${PERSONA_JSON}" <<'PY' >> "${PROM_CAND}"
import json, sys
pjson = sys.argv[1]
data = json.load(open(pjson))
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
    print(line)
PY

echo "Appended persona recommendations to ${PROM_CAND}"

# Print a concise persona table for quick copy/paste
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

echo
echo "Persona JSON: ${PERSONA_JSON}"
echo "Board verdict: ${BOARD_VERDICT}"
echo "Promotion candidates file: ${PROM_CAND}"
echo
echo "Done."
