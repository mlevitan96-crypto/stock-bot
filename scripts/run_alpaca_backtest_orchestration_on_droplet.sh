#!/usr/bin/env bash
# ALPACA SIMULATION BACKTEST ORCHESTRATION WITH PLUGIN EVIDENCE BUNDLE
# Contract: DROPLET canonical (/root/stock-bot). Simulation (enrich_signal->compute_composite_score_v2). Multi-model (prosecutor/defender/SRE/board).
# Plugins: evidence bundle in multi_model/evidence for SRE. No lookahead (lab-mode; bars with t <= decision_ts - decision_latency_seconds).
# Artifacts: config.json, provenance.json, metrics.json, trades.csv, backtest_trades.jsonl, summary/summary.md, multi_model/board_verdict.md+json, FINAL_VERDICT.txt.
set -eu

cd /root/stock-bot || exit 1
export RUN_TS=$(date -u +"%Y%m%dT%H%M%SZ")
export RUN_ID="alpaca_backtest_${RUN_TS}"
export RUN_ID
mkdir -p reports/backtests/${RUN_ID}
mkdir -p reports/governance/${RUN_ID}
echo "RUN_ID=${RUN_ID}" > reports/backtests/${RUN_ID}/run_meta.txt

# 0. One-time prep: ensure all required scripts exist
python3 scripts/check_backtest_scripts_present.py --out-dir reports/backtests/${RUN_ID} || {
  echo "ERROR: Missing scripts. See reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md"
  exit 1
}

# 1. Preflight: plugin and data discovery (plugins-aware for SRE evidence)
echo "=== PREFLIGHT CHECK ===" > reports/backtests/${RUN_ID}/preflight.txt
if [ -d plugins ]; then
  echo "plugins:" >> reports/backtests/${RUN_ID}/preflight.txt
  ls -1 plugins >> reports/backtests/${RUN_ID}/preflight.txt 2>/dev/null || true
else
  echo "no plugins dir" >> reports/backtests/${RUN_ID}/preflight.txt
fi
if find data -type f -name "*alpaca*" -print -quit 2>/dev/null | grep -q .; then
  echo "Alpaca bars present" >> reports/backtests/${RUN_ID}/preflight.txt
  find data -maxdepth 3 -type f -name "*alpaca*" -print >> reports/backtests/${RUN_ID}/preflight.txt 2>/dev/null || true
else
  echo "WARNING: No Alpaca bars found; will create manifest-only snapshot" >> reports/backtests/${RUN_ID}/preflight.txt
fi
if [ -d data/bars ]; then
  echo "data/bars present:" >> reports/backtests/${RUN_ID}/preflight.txt
  find data/bars -maxdepth 2 -type f -name "*.json" -print 2>/dev/null | head -30 >> reports/backtests/${RUN_ID}/preflight.txt || true
fi

# 2. Governance preflight (provenance + config)
python3 - <<PY 2>&1 | tee reports/backtests/${RUN_ID}/bootstrap_stdout.log
import json, os, subprocess, datetime
outdir = os.path.join("reports", "backtests", os.environ["RUN_ID"])
os.makedirs(outdir, exist_ok=True)
cfg = {
  "data_snapshot": None,
  "lab_mode": True,
  "decision_latency_seconds": 60,
  "min_exec_score": 1.8,
  "slippage_model": {"type": "pct", "value": 0.0005},
  "commission_per_trade": 0.005,
  "borrow_cost_annual_pct": 0.05,
  "walkforward": {"train_months": 3, "test_months": 1},
  "random_seed": 42
}
try:
  git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
except Exception:
  git_commit = "unknown"
prov = {"git_commit": git_commit, "timestamp": datetime.datetime.utcnow().isoformat() + "Z", "config": cfg}
with open(os.path.join(outdir, "provenance.json"), "w") as f:
  json.dump(prov, f, indent=2)
with open(os.path.join(outdir, "config.json"), "w") as f:
  json.dump(cfg, f, indent=2)
with open(os.path.join(outdir, "preflight_ok"), "w") as f:
  f.write("OK")
print("Governance preflight written")
PY

# 3. Create deterministic Alpaca 1m snapshot (or manifest)
mkdir -p data/snapshots
SNAPSHOT="data/snapshots/alpaca_1m_snapshot_${RUN_TS}.tar.gz"
export SNAPSHOT
python3 scripts/prep_alpaca_bars_snapshot.py --out "${SNAPSHOT}" || {
  echo "SNAPSHOT_FAILED" > reports/backtests/${RUN_ID}/SNAPSHOT_ERROR.txt
  echo '{"manifest":"no_bars"}' > reports/backtests/${RUN_ID}/data_snapshot_manifest.json
}
echo "${SNAPSHOT}" > reports/backtests/${RUN_ID}/data_snapshot.txt
python3 - <<PY
import json, os
run_id = os.environ.get("RUN_ID", "")
snap = os.environ.get("SNAPSHOT", "")
p = os.path.join("reports", "backtests", run_id, "provenance.json")
with open(p) as f:
  prov = json.load(f)
prov["config"] = prov.get("config") or {}
prov["config"]["data_snapshot"] = snap
with open(p, "w") as f:
  json.dump(prov, f, indent=2)
print("Provenance updated with snapshot")
PY

# 4. Baseline simulation backtest (lab-mode, deterministic, enrich_signal -> compute_composite_score_v2)
mkdir -p reports/backtests/${RUN_ID}/baseline
if [ ! -f scripts/run_simulation_backtest_on_droplet.py ]; then
  echo "MISSING simulation runner" > reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md
  exit 1
fi
python3 scripts/run_simulation_backtest_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --config configs/backtest_config.json \
  --out reports/backtests/${RUN_ID}/baseline \
  --lab-mode \
  --min-exec-score 1.8 || {
  echo "BASELINE_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}

# 5. Event studies (lab-mode)
mkdir -p reports/backtests/${RUN_ID}/event_studies
python3 scripts/run_event_studies_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --lab-mode \
  --horizons 1,5,15,60,1440,4320 \
  --out reports/backtests/${RUN_ID}/event_studies || {
  echo "EVENT_STUDIES_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}

# 6. Param sweep orchestration (coarse); create param_grid.json if missing
mkdir -p reports/backtests/${RUN_ID}/param_sweep
mkdir -p configs
if [ ! -f configs/param_grid.json ]; then
  cat > configs/param_grid.json <<'JSON'
{"min_exec_score":[1.5,1.8,2.0,2.5],"flow_weight_scale":[0.5,1.0,1.5],"freshness_multiplier":[0.5,1.0,1.5],"toxicity_penalty_scale":[0.5,1.0,1.5],"hold_floor_pct":[0.25,0.5]}
JSON
fi
python3 scripts/param_sweep_orchestrator.py \
  --bars "${SNAPSHOT}" \
  --param-grid configs/param_grid.json \
  --parallel 8 \
  --lab-mode \
  --out reports/backtests/${RUN_ID}/param_sweep || {
  echo "PARAM_SWEEP_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}

# 7. Adversarial perturbations and blocked-winner forensics
mkdir -p reports/backtests/${RUN_ID}/adversarial
python3 scripts/run_adversarial_tests_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --perturbations zero,invert,delay \
  --out reports/backtests/${RUN_ID}/adversarial || {
  echo "ADVERSARIAL_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}

# 8. Collect plugin outputs and build SRE evidence bundle
mkdir -p reports/backtests/${RUN_ID}/multi_model/evidence
if [ -d plugins ]; then ls -1 plugins > reports/backtests/${RUN_ID}/multi_model/plugins.txt 2>/dev/null || true; else echo "no_plugins" > reports/backtests/${RUN_ID}/multi_model/plugins.txt; fi
for f in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json data/uw_cache.json data/plugins_output.json data/bars_manifest.json; do
  if [ -f "$f" ]; then
    cp -v "$f" reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
  fi
done
# Attach baseline trades and summary for context
cp -v reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
cp -v reports/backtests/${RUN_ID}/baseline/backtest_summary.json reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
ls -1 reports/backtests/${RUN_ID}/multi_model/evidence 2>/dev/null > reports/backtests/${RUN_ID}/multi_model/evidence_manifest.txt || true

# 9. Multi-model adversarial review (mandatory) using evidence bundle
mkdir -p reports/backtests/${RUN_ID}/multi_model
if [ ! -f scripts/multi_model_runner.py ]; then
  echo "MISSING multi_model_runner" > reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md
  exit 1
fi
python3 scripts/multi_model_runner.py \
  --backtest_dir reports/backtests/${RUN_ID} \
  --roles prosecutor,defender,sre,board \
  --evidence reports/backtests/${RUN_ID}/multi_model/evidence \
  --out reports/backtests/${RUN_ID}/multi_model || {
  echo "MULTI_MODEL_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}
if [ ! -f reports/backtests/${RUN_ID}/multi_model/board_verdict.json ]; then
  echo "MULTI_MODEL_VERDICT_MISSING" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
fi

# 10. Exit optimization sweep
mkdir -p reports/backtests/${RUN_ID}/exits
python3 scripts/run_exit_optimization_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --config configs/backtest_config.json \
  --out reports/backtests/${RUN_ID}/exits || {
  echo "EXIT_OPT_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}

# 11. Summarize and governance artifacts
python3 scripts/generate_backtest_summary.py --dirs "reports/backtests/${RUN_ID}/*" --out reports/backtests/${RUN_ID}/summary || {
  echo "SUMMARY_GEN_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}
python3 scripts/run_governance_full.py --backtest reports/backtests/${RUN_ID}/summary --out reports/governance/${RUN_ID} || {
  echo "GOVERNANCE_RUN_FAILED" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
}

# 12. Final acceptance checks
ACCEPT=0
if [ -f reports/backtests/${RUN_ID}/provenance.json ] && \
   [ -f reports/backtests/${RUN_ID}/summary/summary.md ]; then
  if [ -f reports/backtests/${RUN_ID}/baseline/backtest_summary.json ] || [ -f reports/backtests/${RUN_ID}/baseline/metrics.json ]; then
    ACCEPT=1
  fi
fi

# 13. Final verdict and key metrics
if [ "${ACCEPT}" -eq 1 ]; then
  echo "FINAL_VERDICT: BACKTEST_RUN_OK" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Run ID: ${RUN_ID}"
  python3 - <<PY
import json, os
run_id = os.environ.get("RUN_ID", "")
mfile = os.path.join("reports", "backtests", run_id, "baseline", "metrics.json")
if not os.path.exists(mfile):
  mfile = os.path.join("reports", "backtests", run_id, "baseline", "backtest_summary.json")
try:
  m = json.load(open(mfile))
  out = {"gate_p10": m.get("gate_p10"), "gate_p50": m.get("gate_p50"), "gate_p90": m.get("gate_p90"), "net_pnl": m.get("net_pnl")}
  print("KEY_METRICS:", json.dumps(out))
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
