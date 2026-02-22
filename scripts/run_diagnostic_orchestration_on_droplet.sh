#!/usr/bin/env bash
# FULL DIAGNOSTIC ORCHESTRATION (DROPLET ONLY, CURSOR-FIRST, MULTI-MODEL, PLUGINS AWARE, ADVERSARIAL)
# Contract: simulation emits direction, attribution_components, diverse exits; per-signal attribution, ablation,
# exec sensitivity, exit sweep, param sweep, blocked-trade analysis, SRE evidence bundle, multi-model verdict.
# Artifacts: config.json, provenance.json, baseline/*, attribution/per_signal_pnl.json, ablation/ablation_summary.json,
# exec_sensitivity/exec_sensitivity.json, exit_sweep/exit_sweep_summary.json, param_sweep/pareto_frontier.json,
# multi_model/board_verdict.md, governance/backtest_governance_report.json.
set -eu

cd /root/stock-bot || exit 1
export RUN_TS=$(date -u +"%Y%m%dT%H%M%SZ")
export RUN_ID="alpaca_diag_${RUN_TS}"
mkdir -p reports/backtests/${RUN_ID}
mkdir -p reports/governance/${RUN_ID}
echo "RUN_ID=${RUN_ID}" > reports/backtests/${RUN_ID}/run_meta.txt

# 0. Precondition: required scripts (fail fast)
python3 scripts/check_diagnostic_scripts_present.py --out-dir reports/backtests/${RUN_ID} || {
  echo "ERROR: Missing scripts. See reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md"
  exit 1
}

# 1. Preflight: plugins + data discovery
echo "=== PREFLIGHT CHECK ===" > reports/backtests/${RUN_ID}/preflight.txt
if [ -d plugins ]; then echo "plugins:" >> reports/backtests/${RUN_ID}/preflight.txt; ls -1 plugins >> reports/backtests/${RUN_ID}/preflight.txt 2>/dev/null || true; else echo "no plugins dir" >> reports/backtests/${RUN_ID}/preflight.txt; fi
if find data -type f -name "*alpaca*" -print -quit 2>/dev/null | grep -q .; then
  echo "Alpaca bars present" >> reports/backtests/${RUN_ID}/preflight.txt
  find data -maxdepth 3 -type f -name "*alpaca*" -print >> reports/backtests/${RUN_ID}/preflight.txt 2>/dev/null || true
else
  echo "WARNING: No Alpaca bars found; will create manifest-only snapshot" >> reports/backtests/${RUN_ID}/preflight.txt
fi
for pf in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json; do
  if [ -f "$pf" ]; then echo "FOUND: $pf" >> reports/backtests/${RUN_ID}/preflight.txt; fi
done

# 2. Governance preflight: provenance + config
python3 - <<'PY' 2>&1 | tee -a reports/backtests/${RUN_ID}/bootstrap_stdout.log
import json, os, subprocess, datetime
out = os.environ.get("RUN_ID", "")
if not out:
    raise SystemExit("RUN_ID not set")
outdir = os.path.join("reports", "backtests", out)
os.makedirs(outdir, exist_ok=True)
cfg = {
  "data_snapshot": None,
  "lab_mode": True,
  "decision_latency_seconds": 60,
  "min_exec_score": 1.8,
  "slippage_model": {"type":"pct","value":0.0005},
  "commission_per_trade": 0.005,
  "borrow_cost_annual_pct": 0.05,
  "walkforward": {"train_months":3,"test_months":1},
  "random_seed": 42
}
try:
  git_commit = subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
except Exception:
  git_commit = "unknown"
prov = {"git_commit": git_commit, "timestamp": datetime.datetime.utcnow().isoformat()+"Z", "config": cfg}
with open(os.path.join(outdir,"provenance.json"),"w") as f:
  json.dump(prov, f, indent=2)
with open(os.path.join(outdir,"config.json"),"w") as f:
  json.dump(cfg, f, indent=2)
with open(os.path.join(outdir,"preflight_ok"),"w") as f:
  f.write("OK")
print("Governance preflight written")
PY

# 3. Snapshot (deterministic) or manifest-only
mkdir -p data/snapshots
SNAPSHOT="data/snapshots/alpaca_1m_snapshot_${RUN_TS}.tar.gz"
export SNAPSHOT
python3 scripts/prep_alpaca_bars_snapshot.py --out "${SNAPSHOT}" || {
  echo "SNAPSHOT_FAILED" > reports/backtests/${RUN_ID}/SNAPSHOT_ERROR.txt
  echo '{"manifest":"no_bars"}' > reports/backtests/${RUN_ID}/data_snapshot_manifest.json
}
echo "${SNAPSHOT}" > reports/backtests/${RUN_ID}/data_snapshot.txt
python3 - <<'PY'
import json, os
run_id = os.environ.get("RUN_ID", "")
snap = os.environ.get("SNAPSHOT", "")
p = os.path.join("reports", "backtests", run_id, "provenance.json")
with open(p) as f:
  prov = json.load(f)
prov.setdefault("config", {})["data_snapshot"] = snap
with open(p, "w") as f:
  json.dump(prov, f, indent=2)
print("Provenance updated with snapshot")
PY

# 4. Baseline simulation (must emit attribution_components, direction, diverse exits)
mkdir -p reports/backtests/${RUN_ID}/baseline
python3 scripts/run_simulation_backtest_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --config configs/backtest_config.json \
  --out reports/backtests/${RUN_ID}/baseline \
  --lab-mode \
  --min-exec-score 1.8 || {
    echo "BASELINE_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
    exit 1
}

# 5. Event studies
mkdir -p reports/backtests/${RUN_ID}/event_studies
python3 scripts/run_event_studies_on_droplet.py --bars "${SNAPSHOT}" --lab-mode --horizons 1,5,15,60,1440,4320 --out reports/backtests/${RUN_ID}/event_studies || {
  echo "EVENT_STUDIES_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# 6. Per-signal attribution
mkdir -p reports/backtests/${RUN_ID}/attribution
python3 scripts/compute_per_signal_attribution.py \
  --trades reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl \
  --out reports/backtests/${RUN_ID}/attribution/per_signal_pnl.json || {
  echo "ATTRIBUTION_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# 7. Ablation suite
mkdir -p reports/backtests/${RUN_ID}/ablation
python3 scripts/run_signal_ablation_suite.py \
  --trades reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl \
  --perturbations zero,invert \
  --out reports/backtests/${RUN_ID}/ablation || {
  echo "ABLATION_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# 8. Execution sensitivity
mkdir -p reports/backtests/${RUN_ID}/exec_sensitivity
python3 scripts/run_exec_sensitivity.py \
  --bars "${SNAPSHOT}" \
  --config configs/backtest_config.json \
  --slippage-multipliers 0.0,1.0,2.0 \
  --out reports/backtests/${RUN_ID}/exec_sensitivity || {
  echo "EXEC_SENSITIVITY_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# 9. Exit optimization sweep
mkdir -p reports/backtests/${RUN_ID}/exit_sweep
python3 scripts/run_exit_optimization_on_droplet.py --bars "${SNAPSHOT}" --config configs/backtest_config.json --out reports/backtests/${RUN_ID}/exit_sweep || {
  echo "EXIT_SWEEP_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
if [ ! -f reports/backtests/${RUN_ID}/exit_sweep/exit_sweep_summary.json ]; then
  [ -f reports/backtests/${RUN_ID}/exit_sweep/exit_sweep.json ] && cp reports/backtests/${RUN_ID}/exit_sweep/exit_sweep.json reports/backtests/${RUN_ID}/exit_sweep/exit_sweep_summary.json || true
fi

# 10. Param sweep
mkdir -p reports/backtests/${RUN_ID}/param_sweep
if [ ! -f configs/param_grid.json ]; then
  cat > configs/param_grid.json <<'JSON'
{"min_exec_score":[1.5,1.8,2.0,2.5],"flow_weight_scale":[0.5,1.0,1.5],"freshness_multiplier":[0.5,1.0,1.5],"toxicity_penalty_scale":[0.5,1.0,1.5],"hold_floor_pct":[0.25,0.5],"time_stop_minutes":[15,60,240]}
JSON
fi
python3 scripts/param_sweep_orchestrator.py --bars "${SNAPSHOT}" --param-grid configs/param_grid.json --parallel 8 --lab-mode --out reports/backtests/${RUN_ID}/param_sweep || {
  echo "PARAM_SWEEP_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
if [ ! -f reports/backtests/${RUN_ID}/param_sweep/pareto_frontier.json ]; then
  python3 -c "
import json, os
from pathlib import Path
run_id = os.environ.get('RUN_ID', '')
p = Path('reports/backtests') / run_id / 'param_sweep'
r = p / 'results.json'
if r.exists():
  d = json.loads(r.read_text())
  pf = [x for x in d.get('runs', []) if isinstance(x, dict)]
else:
  pf = []
(p / 'pareto_frontier.json').write_text(json.dumps({'pareto_frontier': pf, 'status': 'derived'}, indent=2))
"
fi

# 11. Adversarial perturbations
mkdir -p reports/backtests/${RUN_ID}/adversarial
python3 scripts/run_adversarial_tests_on_droplet.py --bars "${SNAPSHOT}" --perturbations zero,invert,delay --out reports/backtests/${RUN_ID}/adversarial || true

# 12. Blocked-trade opportunity-cost analysis
mkdir -p reports/backtests/${RUN_ID}/blocked_analysis
if [ -f scripts/run_blocked_trade_analysis.py ]; then
  python3 scripts/run_blocked_trade_analysis.py --blocked state/blocked_trades.jsonl --executed reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl --out reports/backtests/${RUN_ID}/blocked_analysis 2>/dev/null || true
else
  echo "MISSING run_blocked_trade_analysis.py; skipping blocked analysis" > reports/backtests/${RUN_ID}/blocked_analysis/NOTICE.txt
fi

# 13. SRE evidence bundle
mkdir -p reports/backtests/${RUN_ID}/multi_model/evidence
if [ -d plugins ]; then ls -1 plugins > reports/backtests/${RUN_ID}/multi_model/plugins.txt 2>/dev/null || true; else echo "no_plugins" > reports/backtests/${RUN_ID}/multi_model/plugins.txt; fi
for f in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json data/uw_cache.json data/plugins_output.json data/bars_manifest.json; do
  if [ -f "$f" ]; then cp "$f" reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true; fi
done
cp reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
cp reports/backtests/${RUN_ID}/baseline/backtest_summary.json reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
ls -1 reports/backtests/${RUN_ID}/multi_model/evidence 2>/dev/null > reports/backtests/${RUN_ID}/multi_model/evidence_manifest.txt || true

# 14. Multi-model adversarial review
python3 scripts/multi_model_runner.py --backtest_dir reports/backtests/${RUN_ID} --roles prosecutor,defender,sre,board --evidence reports/backtests/${RUN_ID}/multi_model/evidence --out reports/backtests/${RUN_ID}/multi_model || {
  echo "MULTI_MODEL_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
if [ ! -f reports/backtests/${RUN_ID}/multi_model/board_verdict.json ]; then
  echo "MULTI_MODEL_VERDICT_MISSING" >> reports/backtests/${RUN_ID}/ERROR.txt
fi

# 15. Summarize and governance
python3 scripts/generate_backtest_summary.py --dirs "reports/backtests/${RUN_ID}/*" --out reports/backtests/${RUN_ID}/summary || {
  echo "SUMMARY_GEN_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
python3 scripts/run_governance_full.py --backtest reports/backtests/${RUN_ID}/summary --out reports/governance/${RUN_ID} || {
  echo "GOVERNANCE_RUN_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# 16. Final acceptance
ACCEPT=0
if [ -f reports/backtests/${RUN_ID}/provenance.json ] && [ -f reports/backtests/${RUN_ID}/summary/summary.md ]; then
  if [ -f reports/backtests/${RUN_ID}/baseline/backtest_summary.json ] || [ -f reports/backtests/${RUN_ID}/baseline/metrics.json ]; then
    ACCEPT=1
  fi
fi

# 17. Final verdict
if [ "${ACCEPT}" -eq 1 ]; then
  echo "FINAL_VERDICT: BACKTEST_RUN_OK" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Run ID: ${RUN_ID}"
  python3 - <<'PY'
import json, os
run_id = os.environ.get("RUN_ID", "")
mfile = os.path.join("reports", "backtests", run_id, "baseline", "metrics.json")
try:
  m = json.load(open(mfile))
  print("KEY_METRICS:", json.dumps({"gate_p10": m.get("gate_p10"), "gate_p50": m.get("gate_p50"), "gate_p90": m.get("gate_p90"), "net_pnl": m.get("net_pnl")}))
except Exception as e:
  print("KEY_METRICS: missing or unreadable", e)
PY
else
  echo "FINAL_VERDICT: BACKTEST_RUN_FAILED" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Check reports/backtests/${RUN_ID}/ERROR.txt and bootstrap logs."
  exit 2
fi

echo "DONE. Artifacts under reports/backtests/${RUN_ID} and reports/governance/${RUN_ID}"
exit 0
