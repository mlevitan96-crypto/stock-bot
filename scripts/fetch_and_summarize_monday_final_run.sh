#!/usr/bin/env bash
# FETCH, VALIDATE, AND SUMMARIZE MONDAY FINAL RUN (RUN_ID alpaca_monday_final_20260222T174120Z)
# Run on droplet at /root/stock-bot.
set -euo pipefail
cd /root/stock-bot || { echo "Repo root missing"; exit 1; }

RUN_ID="alpaca_monday_final_20260222T174120Z"
RUN_DIR="reports/backtests/${RUN_ID}"
OUT_SUMMARY="${RUN_DIR}/cursor_quick_summary.md"

echo "Checking FINAL_VERDICT..."
if [ -f "${RUN_DIR}/FINAL_VERDICT.txt" ]; then
  cat "${RUN_DIR}/FINAL_VERDICT.txt"
else
  echo "FINAL_VERDICT.txt missing; check /tmp/monday_final.log"
fi

echo "Collecting key artifacts list..."
ls -la "${RUN_DIR}" 2>/dev/null || true
echo "" > "${OUT_SUMMARY}"
echo "# Quick Cursor Summary for ${RUN_ID}" >> "${OUT_SUMMARY}"
echo "" >> "${OUT_SUMMARY}"

# 1. Key metrics
METRICS="${RUN_DIR}/baseline/metrics.json"
if [ -f "${METRICS}" ]; then
  echo "Baseline metrics:" >> "${OUT_SUMMARY}"
  jq '{net_pnl, trades_count, win_rate_pct, gate_p10, gate_p50, gate_p90}' "${METRICS}" >> "${OUT_SUMMARY}" 2>/dev/null || cat "${METRICS}" >> "${OUT_SUMMARY}"
else
  echo "Baseline metrics missing" >> "${OUT_SUMMARY}"
fi

# 2. Schema smoke test on sample trades (diagnostic file preferred)
TRADES_DIAG="${RUN_DIR}/baseline/backtest_trades_diagnostic.jsonl"
TRADES_RAW="${RUN_DIR}/baseline/backtest_trades.jsonl"
TRADES_FILE="${TRADES_DIAG}"
if [ ! -f "${TRADES_DIAG}" ]; then TRADES_FILE="${TRADES_RAW}"; fi

echo "" >> "${OUT_SUMMARY}"
echo "Schema smoke test (sample up to 200 trades):" >> "${OUT_SUMMARY}"
python3 - <<PY >> "${OUT_SUMMARY}" 2>&1
import json
f="${TRADES_FILE}"
req=["entry_score","direction","context","exit_reason"]
count=0
missing=set()
try:
    with open(f) as fh:
        for i,line in enumerate(fh):
            if i>=200: break
            j=json.loads(line)
            count+=1
            if "entry_score" not in j: missing.add("entry_score")
            if "direction" not in j: missing.add("direction")
            ctx=j.get("context",{})
            if "attribution_components" not in ctx: missing.add("context.attribution_components")
            if "exit_reason" not in j: missing.add("exit_reason")
except Exception as e:
    print("ERROR reading trades:",e)
print("sample_count",count)
print("missing_fields_sample",sorted(list(missing)))
PY

# 3. Top 10 per-signal contributors (if present)
ATTR="${RUN_DIR}/attribution/per_signal_pnl.json"
echo "" >> "${OUT_SUMMARY}"
echo "Top per-signal contributors (top 10) if available:" >> "${OUT_SUMMARY}"
if [ -f "${ATTR}" ]; then
  jq 'sort_by(-.net_pnl) | .[:10] | map({signal_id:.signal_id, net_pnl:.net_pnl, trade_count:.trade_count})' "${ATTR}" >> "${OUT_SUMMARY}" 2>/dev/null || cat "${ATTR}" >> "${OUT_SUMMARY}"
else
  echo "per_signal_pnl.json missing" >> "${OUT_SUMMARY}"
fi

# 4. Ablation fragility check (does any ablation flip sign)
ABL="${RUN_DIR}/ablation/ablation_summary.json"
echo "" >> "${OUT_SUMMARY}"
echo "Ablation fragility check (top flips) if available:" >> "${OUT_SUMMARY}"
if [ -f "${ABL}" ]; then
  jq '.signals | to_entries | map({signal_id: .key, zero: .value.zero, invert: .value.invert}) | .[:10]' "${ABL}" >> "${OUT_SUMMARY}" 2>/dev/null || cat "${ABL}" >> "${OUT_SUMMARY}"
else
  echo "ablation_summary.json missing" >> "${OUT_SUMMARY}"
fi

# 5. Exec sensitivity quick check
EXEC="${RUN_DIR}/exec_sensitivity/exec_sensitivity.json"
echo "" >> "${OUT_SUMMARY}"
echo "Execution sensitivity (0x vs 2x) if available:" >> "${OUT_SUMMARY}"
if [ -f "${EXEC}" ]; then
  jq '.' "${EXEC}" >> "${OUT_SUMMARY}" 2>/dev/null || cat "${EXEC}" >> "${OUT_SUMMARY}"
else
  echo "exec_sensitivity.json missing" >> "${OUT_SUMMARY}"
fi

# 6. Exit sweep summary
EXIT="${RUN_DIR}/exit_sweep/exit_sweep_summary.json"
if [ ! -f "${EXIT}" ]; then EXIT="${RUN_DIR}/exit_sweep/exit_sweep.json"; fi
echo "" >> "${OUT_SUMMARY}"
echo "Exit sweep summary (MFE/MAE) if available:" >> "${OUT_SUMMARY}"
if [ -f "${EXIT}" ]; then
  jq '.' "${EXIT}" >> "${OUT_SUMMARY}" 2>/dev/null || cat "${EXIT}" >> "${OUT_SUMMARY}"
else
  echo "exit_sweep_summary.json missing" >> "${OUT_SUMMARY}"
fi

# 7. Multi-model verdict and evidence manifest
MM_VER="${RUN_DIR}/multi_model/board_verdict.md"
MM_PLUG="${RUN_DIR}/multi_model/plugins.txt"
echo "" >> "${OUT_SUMMARY}"
echo "Multi-model verdict and evidence:" >> "${OUT_SUMMARY}"
if [ -f "${MM_VER}" ]; then
  echo "Board verdict (top lines):" >> "${OUT_SUMMARY}"
  head -n 40 "${MM_VER}" >> "${OUT_SUMMARY}" 2>/dev/null || cat "${MM_VER}" >> "${OUT_SUMMARY}"
else
  echo "multi_model/board_verdict.md missing" >> "${OUT_SUMMARY}"
fi
if [ -f "${MM_PLUG}" ]; then
  echo "" >> "${OUT_SUMMARY}"
  echo "Plugins manifest:" >> "${OUT_SUMMARY}"
  cat "${MM_PLUG}" >> "${OUT_SUMMARY}"
else
  echo "multi_model/plugins.txt missing" >> "${OUT_SUMMARY}"
fi

# 8. Customer advocate and NEXT_STEPS
echo "" >> "${OUT_SUMMARY}"
echo "Customer advocate summary (first 40 lines):" >> "${OUT_SUMMARY}"
if [ -f "${RUN_DIR}/customer_advocate.md" ]; then head -n 40 "${RUN_DIR}/customer_advocate.md" >> "${OUT_SUMMARY}"; else echo "customer_advocate.md missing" >> "${OUT_SUMMARY}"; fi
echo "" >> "${OUT_SUMMARY}"
echo "NEXT_STEPS (first 40 lines):" >> "${OUT_SUMMARY}"
if [ -f "${RUN_DIR}/NEXT_STEPS.md" ]; then head -n 40 "${RUN_DIR}/NEXT_STEPS.md" >> "${OUT_SUMMARY}"; else echo "NEXT_STEPS.md missing" >> "${OUT_SUMMARY}"; fi

# 9. Governance report path
echo "" >> "${OUT_SUMMARY}"
echo "Governance report path:" >> "${OUT_SUMMARY}"
ls -la "reports/governance/" 2>/dev/null | grep "${RUN_ID}" || true >> "${OUT_SUMMARY}"

# 10. Print summary path and tail of final logs
echo "" >> "${OUT_SUMMARY}"
echo "Summary written to ${OUT_SUMMARY}" >> "${OUT_SUMMARY}"
echo "Tail of orchestration log (last 200 lines):" >> "${OUT_SUMMARY}"
tail -n 200 /tmp/monday_final.log >> "${OUT_SUMMARY}" 2>/dev/null || echo "orchestration log not found" >> "${OUT_SUMMARY}"

# 11. Output the summary to stdout for quick copy/paste
cat "${OUT_SUMMARY}"
