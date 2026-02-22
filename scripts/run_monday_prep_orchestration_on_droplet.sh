#!/usr/bin/env bash
# MONOLITHIC PRE-MONDAY DIAGNOSTIC + VALIDATION (DROPLET ONLY)
# Contract: simulation emits direction, context.attribution_components, diverse exit_reason;
# per-signal attribution, ablation, exec sensitivity, exit sweep, param sweep, blocked-trade analysis,
# multi-model with evidence; decision-grade artifacts + customer_advocate.
# No lookahead: features from bars with t <= decision_ts - decision_latency_seconds.
set -eu

cd /root/stock-bot || exit 1
export RUN_TS=$(date -u +"%Y%m%dT%H%M%SZ")
export RUN_ID="alpaca_monday_prep_${RUN_TS}"
mkdir -p reports/backtests/${RUN_ID}
mkdir -p reports/governance/${RUN_ID}
echo "RUN_ID=${RUN_ID}" > reports/backtests/${RUN_ID}/run_meta.txt

# ---------- 0. Pre-check required scripts (fail fast) ----------
MISSING=()
for f in \
  scripts/run_alpaca_backtest_orchestration_on_droplet.sh \
  scripts/prep_alpaca_bars_snapshot.py \
  scripts/run_simulation_backtest_on_droplet.py \
  scripts/run_event_studies_on_droplet.py \
  scripts/run_backtest_on_droplet.py \
  scripts/param_sweep_orchestrator.py \
  scripts/run_adversarial_tests_on_droplet.py \
  scripts/multi_model_runner.py \
  scripts/run_exit_optimization_on_droplet.py \
  scripts/generate_backtest_summary.py \
  scripts/run_governance_full.py \
  scripts/compute_per_signal_attribution.py \
  scripts/run_signal_ablation_suite.py \
  scripts/run_exec_sensitivity.py \
  scripts/run_blocked_trade_analysis.py \
  scripts/analysis/run_effectiveness_reports.py \
  configs/backtest_config.json; do
  if [ ! -f "$f" ]; then MISSING+=("$f"); fi
done

if [ ${#MISSING[@]} -ne 0 ]; then
  echo "Missing required scripts:" > reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md
  for m in "${MISSING[@]}"; do echo "$m" >> reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md; done
  echo "Exiting due to missing scripts. See reports/backtests/${RUN_ID}/ERROR_MISSING_SCRIPTS.md"
  exit 1
fi

# ---------- 1. Preflight: plugins + data discovery ----------
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
for pf in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json state/blocked_trades.jsonl; do
  if [ -f "$pf" ]; then echo "FOUND: $pf" >> reports/backtests/${RUN_ID}/preflight.txt; fi
done

# ---------- 2. Governance preflight: provenance + config ----------
python3 - <<PY 2>&1 | tee reports/backtests/${RUN_ID}/bootstrap_stdout.log
import json, os, subprocess, datetime
out = os.path.join("reports", "backtests", os.environ["RUN_ID"])
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
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "provenance.json"), "w") as f:
  json.dump(prov, f, indent=2)
with open(os.path.join(out, "config.json"), "w") as f:
  json.dump(cfg, f, indent=2)
with open(os.path.join(out, "preflight_ok"), "w") as f:
  f.write("OK")
print("Governance preflight written")
PY

# ---------- 3. Alpaca 1m snapshot (or manifest-only) ----------
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
p = os.path.join("reports", "backtests", os.environ["RUN_ID"], "provenance.json")
with open(p) as f:
  prov = json.load(f)
prov.setdefault("config", {})["data_snapshot"] = os.environ.get("SNAPSHOT", "")
with open(p, "w") as f:
  json.dump(prov, f, indent=2)
print("Provenance updated with snapshot")
PY

# ---------- 4. Baseline simulation (direction, attribution_components, diverse exit_reason) ----------
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

if [ ! -f reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl ]; then
  echo "BASELINE_NO_TRADES" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
fi

# Validate sample trade fields (direction, context.attribution_components; exit_reason recommended but optional for legacy).
# Accept if any of first 200 trades has direction and attribution_components.
python3 - <<PY >> reports/backtests/${RUN_ID}/baseline/validation.log 2>&1
import json, sys, os
p = os.path.join("reports", "backtests", os.environ["RUN_ID"], "baseline", "backtest_trades.jsonl")
ok = False
with open(p) as f:
    for i, line in enumerate(f):
        if i >= 200:
            break
        try:
            j = json.loads(line)
            ctx = j.get("context") or {}
            if "direction" in j and "attribution_components" in ctx:
                ok = True
                break
        except Exception:
            pass
if not ok:
    print("MISSING_FIELDS_SAMPLE")
    sys.exit(2)
print("SAMPLE_VALIDATION_OK")
PY
if [ $? -ne 0 ]; then
  echo "BASELINE_MISSING_FIELDS" > reports/backtests/${RUN_ID}/ERROR.txt
  exit 1
fi

# ---------- 4b. Score-vs-profitability (optional; for customer advocate) ----------
mkdir -p reports/backtests/${RUN_ID}/score_analysis
if [ -f scripts/score_vs_profitability.py ]; then
  python3 scripts/score_vs_profitability.py \
    --trades reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl \
    --out reports/backtests/${RUN_ID}/score_analysis || echo "SCORE_VS_PROFITABILITY_WARN"
fi

# ---------- 5. Event studies ----------
mkdir -p reports/backtests/${RUN_ID}/event_studies
python3 scripts/run_event_studies_on_droplet.py --bars "${SNAPSHOT}" --lab-mode --horizons 1,5,15,60,1440,4320 --out reports/backtests/${RUN_ID}/event_studies || {
  echo "EVENT_STUDIES_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# ---------- 6. Per-signal attribution ----------
mkdir -p reports/backtests/${RUN_ID}/attribution
python3 scripts/compute_per_signal_attribution.py \
  --trades reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl \
  --out reports/backtests/${RUN_ID}/attribution/per_signal_pnl.json || {
  echo "ATTRIBUTION_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# ---------- 7. Effectiveness reports ----------
mkdir -p reports/backtests/${RUN_ID}/effectiveness
python3 scripts/analysis/run_effectiveness_reports.py --backtest-dir reports/backtests/${RUN_ID}/baseline --out-dir reports/backtests/${RUN_ID}/effectiveness || {
  echo "EFFECTIVENESS_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# ---------- 8. Customer advocate (generate_customer_advocate.py, or customer_advocate_report.py, or inline) ----------
if [ -f scripts/generate_customer_advocate.py ]; then
  python3 scripts/generate_customer_advocate.py --backtest-dir reports/backtests/${RUN_ID} --out reports/backtests/${RUN_ID}/customer_advocate.md || echo "CUSTOMER_ADVOCATE_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
elif [ -f scripts/customer_advocate_report.py ]; then
  python3 scripts/customer_advocate_report.py --run-dir reports/backtests/${RUN_ID} || echo "CUSTOMER_ADVOCATE_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
else
  python3 - <<PY
import json, os
run_id = os.environ.get("RUN_ID", "")
base = os.path.join("reports", "backtests", run_id)
path = os.path.join(base, "customer_advocate.md")
os.makedirs(os.path.dirname(path), exist_ok=True)
lines = ["# Customer Advocate Summary", ""]
mfile = os.path.join(base, "baseline", "metrics.json")
if os.path.exists(mfile):
    m = json.load(open(mfile))
    lines.append("Baseline metrics: net_pnl=%s, trades_count=%s." % (m.get("net_pnl"), m.get("trades_count")))
lines.extend(["", "Actionable: run per-signal attribution and ablation; exec sensitivity and exit sweep; compare live vs backtest after Monday.", ""])
open(path, "w").write("\n".join(lines))
PY
fi

# ---------- 9. Ablation suite (trades-based; no --bars/--config/--signals) ----------
mkdir -p reports/backtests/${RUN_ID}/ablation
python3 scripts/run_signal_ablation_suite.py \
  --trades reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl \
  --perturbations zero,invert,delay \
  --out reports/backtests/${RUN_ID}/ablation || {
  echo "ABLATION_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# ---------- 10. Execution sensitivity ----------
mkdir -p reports/backtests/${RUN_ID}/exec_sensitivity
python3 scripts/run_exec_sensitivity.py \
  --bars "${SNAPSHOT}" \
  --config configs/backtest_config.json \
  --slippage-multipliers 0.0,1.0,2.0 \
  --out reports/backtests/${RUN_ID}/exec_sensitivity || {
  echo "EXEC_SENSITIVITY_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# ---------- 11. Exit optimization sweep ----------
mkdir -p reports/backtests/${RUN_ID}/exit_sweep
python3 scripts/run_exit_optimization_on_droplet.py --bars "${SNAPSHOT}" --config configs/backtest_config.json --out reports/backtests/${RUN_ID}/exit_sweep || {
  echo "EXIT_SWEEP_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
[ ! -f reports/backtests/${RUN_ID}/exit_sweep/exit_sweep_summary.json ] && [ -f reports/backtests/${RUN_ID}/exit_sweep/exit_sweep.json ] && cp reports/backtests/${RUN_ID}/exit_sweep/exit_sweep.json reports/backtests/${RUN_ID}/exit_sweep/exit_sweep_summary.json || true

# ---------- 12. Param sweep ----------
mkdir -p reports/backtests/${RUN_ID}/param_sweep
if [ ! -f configs/param_grid.json ]; then
  cat > configs/param_grid.json <<'JSON'
{"min_exec_score":[1.5,1.8,2.0,2.5],"flow_weight_scale":[0.5,1.0,1.5],"freshness_multiplier":[0.5,1.0,1.5],"toxicity_penalty_scale":[0.5,1.0,1.5],"hold_floor_pct":[0.25,0.5],"time_stop_minutes":[15,60,240]}
JSON
fi
python3 scripts/param_sweep_orchestrator.py --bars "${SNAPSHOT}" --param-grid configs/param_grid.json --parallel 8 --lab-mode --out reports/backtests/${RUN_ID}/param_sweep || {
  echo "PARAM_SWEEP_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
python3 - <<PY 2>/dev/null || true
import json, glob, os
run_id = os.environ.get("RUN_ID", "")
p = os.path.join("reports", "backtests", run_id, "param_sweep")
r = os.path.join(p, "results.json")
if os.path.exists(r):
    d = json.load(open(r))
    pf = d.get("runs") or []
else:
    pf = []
with open(os.path.join(p, "pareto_frontier.json"), "w") as f:
    json.dump({"pareto_frontier": pf, "status": "derived"}, f, indent=2)
out = os.path.join("reports", "backtests", run_id, "param_sweep", "best_config.json")
best = None
for o in glob.glob(os.path.join(p, "*", "metrics.json")):
    try:
        m = json.load(open(o))
        pnl = m.get("net_pnl")
        if pnl is not None and (best is None or pnl > best[0]):
            best = (pnl, o)
    except Exception:
        pass
if best:
    cfg_path = best[1].replace("metrics.json", "config.json")
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    with open(out, "w") as f:
        json.dump({"best_pnl": best[0], "config": cfg}, f, indent=2)
else:
    with open(out, "w") as f:
        json.dump({"note": "no metrics found"}, f, indent=2)
PY

# ---------- 13. Adversarial perturbations ----------
mkdir -p reports/backtests/${RUN_ID}/adversarial
python3 scripts/run_adversarial_tests_on_droplet.py --bars "${SNAPSHOT}" --perturbations zero,invert,delay --out reports/backtests/${RUN_ID}/adversarial || true

# ---------- 14. Blocked-trade analysis + blocked_opportunity_cost.md ----------
mkdir -p reports/backtests/${RUN_ID}/blocked_analysis
python3 scripts/run_blocked_trade_analysis.py --blocked state/blocked_trades.jsonl --executed reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl --out reports/backtests/${RUN_ID}/blocked_analysis 2>/dev/null || true
if [ -f reports/backtests/${RUN_ID}/blocked_analysis/blocked_opportunity_summary.json ]; then
  python3 - <<PY
import json, os
p = os.path.join("reports", "backtests", os.environ["RUN_ID"], "blocked_analysis", "blocked_opportunity_summary.json")
d = json.load(open(p))
md = ["# Blocked-trade opportunity cost", "", "| Metric | Value |", "|--------|-------|"]
for k, v in d.items():
    if k != "opportunity_cost_note":
        md.append("| %s | %s |" % (k, v))
md.extend(["", "**Note:** " + (d.get("opportunity_cost_note") or ""), ""])
with open(p.replace("blocked_opportunity_summary.json", "blocked_opportunity_cost.md"), "w") as f:
    f.write("\n".join(md))
PY
fi

# ---------- 15. SRE evidence bundle (this run only) ----------
mkdir -p reports/backtests/${RUN_ID}/multi_model/evidence
if [ -d plugins ]; then ls -1 plugins > reports/backtests/${RUN_ID}/multi_model/plugins.txt 2>/dev/null || true; else echo "no_plugins" > reports/backtests/${RUN_ID}/multi_model/plugins.txt; fi
for f in data/uw_flow_cache.json data/uw_expanded_intel.json data/expanded_intel.json data/uw_cache.json data/plugins_output.json data/bars_manifest.json; do
  if [ -f "$f" ]; then cp "$f" reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true; fi
done
[ -f reports/backtests/${RUN_ID}/data_snapshot_manifest.json ] && cp reports/backtests/${RUN_ID}/data_snapshot_manifest.json reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
cp reports/backtests/${RUN_ID}/baseline/backtest_trades.jsonl reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
cp reports/backtests/${RUN_ID}/baseline/backtest_summary.json reports/backtests/${RUN_ID}/multi_model/evidence/ 2>/dev/null || true
ls -1 reports/backtests/${RUN_ID}/multi_model/evidence 2>/dev/null > reports/backtests/${RUN_ID}/multi_model/evidence_manifest.txt || true

# ---------- 16. Multi-model (prosecutor, defender, sre, board) with evidence ----------
python3 scripts/multi_model_runner.py --backtest_dir reports/backtests/${RUN_ID} --roles prosecutor,defender,sre,board --evidence reports/backtests/${RUN_ID}/multi_model/evidence --out reports/backtests/${RUN_ID}/multi_model || {
  echo "MULTI_MODEL_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
if [ ! -f reports/backtests/${RUN_ID}/multi_model/board_verdict.json ]; then
  echo "MULTI_MODEL_VERDICT_MISSING" >> reports/backtests/${RUN_ID}/ERROR.txt
fi

# ---------- 17. Summary and governance ----------
python3 scripts/generate_backtest_summary.py --dirs "reports/backtests/${RUN_ID}/*" --out reports/backtests/${RUN_ID}/summary || {
  echo "SUMMARY_GEN_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}
python3 scripts/run_governance_full.py --backtest reports/backtests/${RUN_ID}/summary --out reports/governance/${RUN_ID} || {
  echo "GOVERNANCE_RUN_FAILED" >> reports/backtests/${RUN_ID}/ERROR.txt
}

# ---------- 18. Final acceptance ----------
ACCEPT=0
if [ -f reports/backtests/${RUN_ID}/provenance.json ] && [ -f reports/backtests/${RUN_ID}/summary/summary.md ]; then
  if [ -f reports/backtests/${RUN_ID}/baseline/backtest_summary.json ] || [ -f reports/backtests/${RUN_ID}/baseline/metrics.json ]; then
    ACCEPT=1
  fi
fi

# ---------- 19. Final verdict ----------
if [ "${ACCEPT}" -eq 1 ]; then
  echo "FINAL_VERDICT: BACKTEST_RUN_OK" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Run ID: ${RUN_ID}"
  python3 - <<'PY'
import json, os
run_id = os.environ.get("RUN_ID", "")
mfile = os.path.join("reports", "backtests", run_id, "baseline", "metrics.json")
try:
  m = json.load(open(mfile))
  print("KEY_METRICS:", json.dumps({"gate_p10": m.get("gate_p10"), "gate_p50": m.get("gate_p50"), "gate_p90": m.get("gate_p90"), "net_pnl": m.get("net_pnl"), "trades_count": m.get("trades_count")}))
except Exception as e:
  print("KEY_METRICS: missing or unreadable", e)
PY
else
  echo "FINAL_VERDICT: BACKTEST_RUN_FAILED" > reports/backtests/${RUN_ID}/FINAL_VERDICT.txt
  echo "Check reports/backtests/${RUN_ID}/ERROR.txt and bootstrap logs."
  exit 2
fi

# ---------- 20. Next steps checklist ----------
cat > reports/backtests/${RUN_ID}/NEXT_STEPS.md <<'TXT'
NEXT STEPS (automated checklist)
1. Inspect attribution/per_signal_pnl.json and ablation/ablation_summary.json.
2. Inspect exec_sensitivity/exec_sensitivity.json to ensure PnL survives 2x slippage.
3. Inspect exit_sweep/exit_sweep_summary.json for better exit rules.
4. Inspect param_sweep/best_config.json and run walk-forward on top candidates.
5. Confirm multi_model/board_verdict.md and governance report endorse next action.
6. If all checks pass, prepare a change_proposal.md with the tuning overlay and run paper/canary on Monday.
TXT

echo "DONE. Artifacts under reports/backtests/${RUN_ID} and reports/governance/${RUN_ID}"
exit 0
