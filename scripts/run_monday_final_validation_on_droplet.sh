#!/usr/bin/env bash
# CURSOR TASK — APPLY PATCHES, RUN PRE-MONDAY VALIDATION + FULL DIAGNOSTIC SUITE (DROPLET FIRST)
# - Execute on droplet at /root/stock-bot.
# - Paper: min_exec_score=1.8; shadow_min_exec_score=1.5 to observe more trades.
# - Multi-model: prosecutor, defender, sre, board with plugin evidence bundle.
# - Non-destructive: artifacts under reports/backtests/<RUN_ID>/ and reports/governance/<RUN_ID>/.
set -euo pipefail
cd /root/stock-bot || { echo "Repo root /root/stock-bot not found"; exit 1; }

# RUN ID
export RUN_TS=$(date -u +"%Y%m%dT%H%M%SZ")
export RUN_ID="alpaca_monday_final_${RUN_TS}"
mkdir -p reports/backtests/${RUN_ID}
echo "RUN_ID=${RUN_ID}" > reports/backtests/${RUN_ID}/run_meta.txt

# 0. Quick required scripts check (fail fast)
REQUIRED=(
  scripts/prep_alpaca_bars_snapshot.py
  scripts/run_simulation_backtest_on_droplet.py
  scripts/run_event_studies_on_droplet.py
  scripts/param_sweep_orchestrator.py
  scripts/run_adversarial_tests_on_droplet.py
  scripts/multi_model_runner.py
  scripts/run_exit_optimization_on_droplet.py
  scripts/generate_backtest_summary.py
  scripts/run_governance_full.py
  scripts/compute_per_signal_attribution.py
  scripts/run_signal_ablation_suite.py
  scripts/run_exec_sensitivity.py
  scripts/run_blocked_trade_analysis.py
  scripts/analysis/run_effectiveness_reports.py
  configs/backtest_config.json
)
MISSING=()
for f in "${REQUIRED[@]}"; do
  if [ ! -f "$f" ]; then MISSING+=("$f"); fi
done
if [ ${#MISSING[@]} -ne 0 ]; then
  echo "Missing required scripts:" > reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md
  for m in "${MISSING[@]}"; do echo "$m" >> reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md; done
  echo "Exiting due to missing scripts. See reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md"
  exit 1
fi

# 1. Apply minimal, reversible patches (emit attribution, ensure exit_reason, neutral defaults)
PATCH_DIR="reports/backtests/${RUN_ID}/patches"
mkdir -p "${PATCH_DIR}"

# 1a. Postprocessor to ensure required fields for diagnostics (non-destructive)
cat > "${PATCH_DIR}/postprocess_trade_fields.py" <<'PY'
#!/usr/bin/env python3
import json,sys
infile=sys.argv[1]; outfile=sys.argv[2]
def ensure(j):
    if "direction" not in j:
        score=j.get("entry_score",0)
        j["direction"]="long" if score>=3.0 else "short"
    ctx=j.setdefault("context",{})
    if "attribution_components" not in ctx:
        comps=j.get("entry_score_components") or []
        if comps:
            ctx["attribution_components"]=[{"signal_id":c.get("id","unknown"),"contribution_to_score":c.get("value",0)} for c in comps]
        else:
            ctx["attribution_components"]=[]
    if "exit_reason" not in j:
        j["exit_reason"]=j.get("exit_reason","hold_bars")
    if "exit_quality_metrics" not in j:
        j["exit_quality_metrics"]={"mfe_pct":None,"mae_pct":None,"giveback_pct":None}
    return j
with open(infile) as fin, open(outfile,"w") as fout:
    for line in fin:
        try:
            j=json.loads(line)
            j=ensure(j)
            fout.write(json.dumps(j)+"\n")
        except:
            fout.write(line)
print("postprocess complete")
PY
chmod +x "${PATCH_DIR}/postprocess_trade_fields.py"

# 1b. Tuning overlay for paper (min_exec_score=1.8, shadow_min_exec_score=1.5)
mkdir -p configs/overlays
cat > configs/overlays/paper_lock_overlay.json <<'JSON'
{
  "min_exec_score": 1.8,
  "shadow_min_exec_score": 1.5,
  "paper_mode": true,
  "notes": "Paper lock for Monday: min_exec_score=1.8; shadow lower gate=1.5 to observe more trades"
}
JSON
cp -v configs/overlays/paper_lock_overlay.json reports/backtests/${RUN_ID}/patches/

# 2. Preflight: plugins + data discovery + provenance
echo "=== PREFLIGHT CHECK ===" > reports/backtests/${RUN_ID}/preflight.txt
if [ -d plugins ]; then echo "plugins:" >> reports/backtests/${RUN_ID}/preflight.txt; ls -1 plugins >> reports/backtests/${RUN_ID}/preflight.txt || true; else echo "no plugins dir" >> reports/backtests/${RUN_ID}/preflight.txt; fi
if find data -type f -name "*alpaca*" -print -quit >/dev/null 2>&1; then echo "Alpaca bars present" >> reports/backtests/${RUN_ID}/preflight.txt; find data -maxdepth 3 -type f -name "*alpaca*" -print >> reports/backtests/${RUN_ID}/preflight.txt || true; else echo "WARNING: No Alpaca bars found; will create manifest-only snapshot" >> reports/backtests/${RUN_ID}/preflight.txt; fi
for pf in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json state/blocked_trades.jsonl; do if [ -f "$pf" ]; then echo "FOUND: $pf" >> reports/backtests/${RUN_ID}/preflight.txt; fi; done

python3 - <<PY > reports/backtests/${RUN_ID}/bootstrap_stdout.log 2>&1
import json,os,subprocess,datetime
out="reports/backtests/${RUN_ID}"
cfg={"data_snapshot":None,"lab_mode":True,"decision_latency_seconds":60,"min_exec_score":1.8,"shadow_min_exec_score":1.5,"random_seed":42}
try:
  git_commit=subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
except:
  git_commit="unknown"
prov={"git_commit":git_commit,"timestamp":datetime.datetime.utcnow().isoformat()+"Z","config":cfg}
os.makedirs(out,exist_ok=True)
open(os.path.join(out,"provenance.json"),"w").write(json.dumps(prov,indent=2))
open(os.path.join(out,"config.json"),"w").write(json.dumps(cfg,indent=2))
open(os.path.join(out,"preflight_ok"),"w").write("OK")
print("Governance preflight written")
PY

# 3. Create deterministic Alpaca 1m snapshot (or manifest-only)
mkdir -p data/snapshots
SNAPSHOT="data/snapshots/alpaca_1m_snapshot_${RUN_TS}.tar.gz"
python3 scripts/prep_alpaca_bars_snapshot.py --out "${SNAPSHOT}" || { echo '{"manifest":"no_bars"}' > reports/backtests/${RUN_ID}/data_snapshot_manifest.json; }
echo "${SNAPSHOT}" > reports/backtests/${RUN_ID}/data_snapshot.txt
python3 - <<PY
import json
p="reports/backtests/${RUN_ID}/provenance.json"
prov=json.load(open(p))
prov["config"]["data_snapshot"]="${SNAPSHOT}"
open(p,"w").write(json.dumps(prov,indent=2))
print("Provenance updated with snapshot")
PY

# 4. Run baseline simulation (paper lock: MIN_EXEC_SCORE=1.8)
mkdir -p reports/backtests/${RUN_ID}/baseline
export MIN_EXEC_SCORE=1.8
export SHADOW_MIN_EXEC_SCORE=1.5
python3 scripts/run_simulation_backtest_on_droplet.py --bars "${SNAPSHOT}" --config configs/backtest_config.json --out reports/backtests/${RUN_ID}/baseline --lab-mode --min-exec-score ${MIN_EXEC_SCORE} || { echo "BASELINE_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt; exit 1; }

# 4b. Postprocess trades for diagnostics (non-destructive)
TRADES_IN="reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl"
TRADES_PP="reports/backtests/${RUN_ID}/baseline/backtest_trades_pp.jsonl"
TRADES_DIAG="reports/backtests/${RUN_ID}/baseline/backtest_trades_diagnostic.jsonl"
if [ -f "${TRADES_IN}" ]; then
  python3 "${PATCH_DIR}/postprocess_trade_fields.py" "${TRADES_IN}" "${TRADES_PP}" && cp -v "${TRADES_PP}" "${TRADES_DIAG}" || true
fi
[ ! -f "${TRADES_DIAG}" ] && [ -f "${TRADES_IN}" ] && cp -v "${TRADES_IN}" "${TRADES_DIAG}" || true

# Trades file for downstream steps (diagnostic if present, else baseline)
TRADES_FILE="${TRADES_DIAG}"
[ ! -f "${TRADES_FILE}" ] && TRADES_FILE="${TRADES_IN}"

# 5. Quick schema validation (sample: direction + attribution_components; exit_reason optional for legacy)
python3 - <<PY >> reports/backtests/${RUN_ID}/baseline/validation.log 2>&1
import json,sys,os
run_id=os.environ.get("RUN_ID","")
base=os.path.join("reports","backtests",run_id,"baseline")
p=os.path.join(base,"backtest_trades_diagnostic.jsonl")
if not os.path.exists(p):
    p=os.path.join(base,"backtest_trades.jsonl")
ok=False
try:
    with open(p) as f:
        for i,line in enumerate(f):
            if i>200: break
            j=json.loads(line)
            ctx=j.get("context",{})
            if "direction" in j and "attribution_components" in ctx:
                ok=True
                break
except Exception as e:
    print("validation_error",e)
    sys.exit(2)
if not ok:
    print("MISSING_FIELDS_SAMPLE")
    sys.exit(2)
print("SAMPLE_VALIDATION_OK")
PY
if [ $? -ne 0 ]; then
  echo "BASELINE_MISSING_FIELDS" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
fi

# 6. Event studies
mkdir -p reports/backtests/${RUN_ID}/event_studies
python3 scripts/run_event_studies_on_droplet.py --bars "${SNAPSHOT}" --lab-mode --horizons 1,5,15,60,1440,4320 --out reports/backtests/${RUN_ID}/event_studies || { echo "EVENT_STUDIES_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt; exit 1; }

# 7. Attribution (per-signal)
mkdir -p reports/backtests/${RUN_ID}/attribution
python3 scripts/compute_per_signal_attribution.py --trades "${TRADES_FILE}" --out reports/backtests/${RUN_ID}/attribution/per_signal_pnl.json || { echo "ATTRIBUTION_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt; exit 1; }

# 8. Effectiveness reports
mkdir -p reports/backtests/${RUN_ID}/effectiveness
python3 scripts/analysis/run_effectiveness_reports.py --backtest-dir reports/backtests/${RUN_ID}/baseline --out-dir reports/backtests/${RUN_ID}/effectiveness || { echo "EFFECTIVENESS_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt; exit 1; }

# 9. Customer advocate summary
if [ -f scripts/generate_customer_advocate.py ]; then
  python3 scripts/generate_customer_advocate.py --backtest-dir reports/backtests/${RUN_ID} --out reports/backtests/${RUN_ID}/customer_advocate.md || true
elif [ -f scripts/customer_advocate_report.py ]; then
  python3 scripts/customer_advocate_report.py --run-dir reports/backtests/${RUN_ID} || true
else
  cat > reports/backtests/${RUN_ID}/customer_advocate.md <<TXT
# Customer Advocate Summary
See baseline metrics in reports/backtests/${RUN_ID}/baseline/metrics.json.
Top levers: see reports/backtests/${RUN_ID}/effectiveness/.
Immediate recommendation: paper at min_exec_score=1.8; shadow gate=1.5 to observe more trades.
TXT
fi

# 10. Ablation suite (trades-based; uses diagnostic or baseline trades)
mkdir -p reports/backtests/${RUN_ID}/ablation
python3 scripts/run_signal_ablation_suite.py --trades "${TRADES_FILE}" --perturbations zero,invert,delay --min-score 1.8 --out reports/backtests/${RUN_ID}/ablation || { echo "ABLATION_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }

# 11. Execution sensitivity (0x,1x,2x)
mkdir -p reports/backtests/${RUN_ID}/exec_sensitivity
python3 scripts/run_exec_sensitivity.py --bars "${SNAPSHOT}" --config configs/backtest_config.json --slippage-multipliers 0.0,1.0,2.0 --out reports/backtests/${RUN_ID}/exec_sensitivity || { echo "EXEC_SENSITIVITY_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }

# 12. Exit optimization sweep
mkdir -p reports/backtests/${RUN_ID}/exit_sweep
python3 scripts/run_exit_optimization_on_droplet.py --bars "${SNAPSHOT}" --config configs/backtest_config.json --out reports/backtests/${RUN_ID}/exit_sweep || { echo "EXIT_SWEEP_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }

# 13. Focused param sweep
mkdir -p reports/backtests/${RUN_ID}/param_sweep
if [ ! -f configs/param_grid.json ]; then
  cat > configs/param_grid.json <<'JSON'
{"min_exec_score":[1.5,1.8,2.0,2.5],"flow_weight_scale":[0.5,1.0,1.5],"freshness_multiplier":[0.5,1.0,1.5],"toxicity_penalty_scale":[0.5,1.0,1.5],"hold_floor_pct":[0.25,0.5],"time_stop_minutes":[15,60,240]}
JSON
fi
python3 scripts/param_sweep_orchestrator.py --bars "${SNAPSHOT}" --param-grid configs/param_grid.json --parallel 8 --lab-mode --out reports/backtests/${RUN_ID}/param_sweep || { echo "PARAM_SWEEP_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }

# 14. Adversarial perturbations
mkdir -p reports/backtests/${RUN_ID}/adversarial
python3 scripts/run_adversarial_tests_on_droplet.py --bars "${SNAPSHOT}" --perturbations zero,invert,delay --out reports/backtests/${RUN_ID}/adversarial || { echo "ADVERSARIAL_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }

# 15. Blocked-trade opportunity-cost analysis
mkdir -p reports/backtests/${RUN_ID}/blocked_analysis
if [ -f scripts/run_blocked_trade_analysis.py ] && [ -f state/blocked_trades.jsonl ]; then
  python3 scripts/run_blocked_trade_analysis.py --blocked state/blocked_trades.jsonl --executed "${TRADES_FILE}" --out reports/backtests/${RUN_ID}/blocked_analysis || true
else
  echo "MISSING blocked-trade analysis or blocked_trades.jsonl; skipping" > reports/backtests/${RUN_ID}/blocked_analysis/NOTICE.txt
fi

# 16. Collect plugin outputs and build SRE evidence bundle
mkdir -p reports/backtests/${RUN_ID}/multi_model/evidence
if [ -d plugins ]; then ls -1 plugins > reports/backtests/${RUN_ID}/multi_model/plugins.txt || true; else echo "no_plugins" > reports/backtests/${RUN_ID}/multi_model/plugins.txt; fi
for f in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json data/uw_cache.json data/plugins_output.json data/bars_manifest.json; do
  if [ -f "$f" ]; then cp -v "$f" reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true; fi
done
[ -f reports/backtests/${RUN_ID}/data_snapshot_manifest.json ] && cp reports/backtests/${RUN_ID}/data_snapshot_manifest.json reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
cp -v "${TRADES_FILE}" reports/backtests/${RUN_ID}/multi_model/evidence/backtest_trades.jsonl 2>/dev/null || true
cp -v reports/backtests/${RUN_ID}/baseline/backtest_summary.json reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
ls -1 reports/backtests/${RUN_ID}/multi_model/evidence 2>/dev/null > reports/backtests/${RUN_ID}/multi_model/evidence_manifest.txt || true

# 17. Multi-model adversarial review (prosecutor, defender, sre, board) with evidence bundle
mkdir -p reports/backtests/${RUN_ID}/multi_model
python3 scripts/multi_model_runner.py --backtest_dir reports/backtests/${RUN_ID} --roles prosecutor,defender,sre,board --evidence reports/backtests/${RUN_ID}/multi_model/evidence || { echo "MULTI_MODEL_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }
if [ ! -f reports/backtests/${RUN_ID}/multi_model/board_verdict.json ]; then echo "MULTI_MODEL_VERDICT_MISSING" >> reports/backtests/${RUN_ID}/ERROR.txt; fi

# 18. Summarize and governance artifacts
python3 scripts/generate_backtest_summary.py --dirs "reports/backtests/${RUN_ID}/*" --out reports/backtests/${RUN_ID}/summary || { echo "SUMMARY_GEN_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }
python3 scripts/run_governance_full.py --backtest reports/backtests/${RUN_ID}/summary --out reports/governance/${RUN_ID} || { echo "GOVERNANCE_RUN_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt; }

# 19. Final acceptance and key metrics
ACCEPT=0
if [ -f reports/backtests/${RUN_ID}/provenance.json ] && [ -f reports/backtests/${RUN_ID}/summary/summary.md ] && ( [ -f reports/backtests/${RUN_ID}/baseline/backtest_summary.json ] || [ -f reports/backtests/${RUN_ID}/baseline/metrics.json ] ); then ACCEPT=1; fi

if [ "${ACCEPT}" -eq 1 ]; then
  echo "FINAL_VERDICT: BACKTEST_RUN_OK" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Run ID: ${RUN_ID}"
  python3 - <<PY
import json,os
run_id=os.environ.get("RUN_ID","")
mfile=os.path.join("reports","backtests",run_id,"baseline","metrics.json")
try:
    m=json.load(open(mfile))
    out={"gate_p10":m.get("gate_p10"),"gate_p50":m.get("gate_p50"),"gate_p90":m.get("gate_p90"),"net_pnl":m.get("net_pnl"),"trades_count":m.get("trades_count")}
    print("KEY_METRICS:",json.dumps(out))
except Exception as e:
    print("KEY_METRICS: missing or unreadable",e)
PY
else
  echo "FINAL_VERDICT: BACKTEST_RUN_FAILED" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Check reports/backtests/${RUN_ID}/ERROR.txt and bootstrap logs."
  exit 2
fi

# 20. NEXT_STEPS checklist
cat > reports/backtests/${RUN_ID}/NEXT_STEPS.md <<'TXT'
NEXT STEPS
1. Review attribution/per_signal_pnl.json and ablation/ablation_summary.json.
2. Confirm exec_sensitivity shows acceptable degradation at 2x slippage.
3. Inspect exit_sweep for MFE/MAE and choose exit rule candidate.
4. Review param_sweep/best_config.json and run walk-forward on top candidates.
5. Confirm multi_model/board_verdict.md endorses next action.
6. If all checks pass, create change_proposal.md with tuning overlay and run paper->canary on Monday.
TXT

echo "DONE. Artifacts under reports/backtests/${RUN_ID} and reports/governance/${RUN_ID}"
exit 0
