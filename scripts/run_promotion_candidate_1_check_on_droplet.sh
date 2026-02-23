#!/usr/bin/env bash
# Promotion candidate 1: focused validation with overlay (dark_pool 0.75, freshness 0.7 + smoothing).
# Run on droplet: cd /root/stock-bot && bash scripts/run_promotion_candidate_1_check_on_droplet.sh
set -euo pipefail
cd /root/stock-bot || { echo "Repo root missing"; exit 1; }

# 1. Ensure repo is up to date and scripts executable
git pull origin main
chmod +x scripts/run_final_finish_on_droplet.sh scripts/run_push_with_plugins_on_droplet.sh scripts/run_finalize_push_on_droplet.sh 2>/dev/null || true

SNAPSHOT="data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz"
if [ ! -f "${SNAPSHOT}" ]; then
  SNAPSHOT=$(ls -t data/snapshots/alpaca_1m_snapshot_*.tar.gz 2>/dev/null | head -1)
  [ -z "${SNAPSHOT}" ] && { echo "No snapshot found"; exit 1; }
  echo "Using snapshot: ${SNAPSHOT}"
fi

# 2. Write the promotion overlay (if not already present)
mkdir -p configs/overlays
cat > configs/overlays/promotion_candidate_1.json <<'JSON'
{
  "composite_weights": {
    "dark_pool": 0.75,
    "freshness_factor": 0.7
  },
  "freshness_smoothing_window": 3,
  "notes": "Promotion candidate: reduce dark_pool by 25% and smooth/lower freshness to reduce single-signal fragility"
}
JSON

# 3. Merge overlay into temp config (simulation has no --overlay; it reads composite_weights from config)
MERGED_CFG="/tmp/promotion_candidate_1_merged.json"
python3 - configs/backtest_config.json configs/overlays/promotion_candidate_1.json "${MERGED_CFG}" <<'PY'
import json, sys
base = json.load(open(sys.argv[1]))
ov = json.load(open(sys.argv[2]))
base.setdefault("composite_weights", {}).update(ov.get("composite_weights", {}))
for k, v in ov.items():
    if k not in ("composite_weights", "notes"):
        base[k] = v
with open(sys.argv[3], "w") as f:
    json.dump(base, f, indent=2)
print("wrote", sys.argv[3])
PY

# 4. Run focused validation using merged config
python3 scripts/run_simulation_backtest_on_droplet.py \
  --bars "${SNAPSHOT}" \
  --config "${MERGED_CFG}" \
  --out reports/backtests/promotion_candidate_1_check \
  --lab-mode \
  --min-exec-score 1.8

# 5. Collect metrics and compare to baseline
echo "=== Promotion candidate 1 metrics ==="
MET="reports/backtests/promotion_candidate_1_check/metrics.json"
[ ! -f "${MET}" ] && MET="reports/backtests/promotion_candidate_1_check/baseline/metrics.json"
if [ -f "${MET}" ]; then
  jq '{net_pnl, trades_count, win_rate_pct}' "${MET}"
else
  echo "No metrics.json found"
fi
echo "=== Baseline (alpaca_monday_final) ==="
jq '{net_pnl, trades_count, win_rate_pct}' reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/metrics.json 2>/dev/null || true

# 6. Exec sensitivity quick check (0x, 1x, 2x base slippage — script uses multipliers)
python3 scripts/run_exec_sensitivity.py \
  --bars "${SNAPSHOT}" \
  --config configs/backtest_config.json \
  --slippage-multipliers 0.0,1.0,2.0 \
  --out reports/backtests/promotion_candidate_1_check/exec_sensitivity || echo "WARN: exec sensitivity failed"

# 7. Bundle evidence and run multi-model
mkdir -p reports/backtests/promotion_candidate_1_check/multi_model/evidence
cp reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_trades.jsonl reports/backtests/promotion_candidate_1_check/multi_model/evidence/ 2>/dev/null || true
MET_SRC="reports/backtests/promotion_candidate_1_check/metrics.json"
[ ! -f "${MET_SRC}" ] && MET_SRC="reports/backtests/promotion_candidate_1_check/baseline/metrics.json"
[ -f "${MET_SRC}" ] && cp "${MET_SRC}" reports/backtests/promotion_candidate_1_check/multi_model/evidence/exp_promotion_candidate_1_metrics.json
cp -v reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/* reports/backtests/promotion_candidate_1_check/multi_model/evidence/ 2>/dev/null || true

python3 scripts/multi_model_runner.py \
  --backtest_dir reports/backtests/alpaca_monday_final_20260222T174120Z \
  --roles prosecutor,defender,sre,board \
  --evidence reports/backtests/promotion_candidate_1_check/multi_model/evidence \
  --out reports/backtests/promotion_candidate_1_check/multi_model/out || echo "WARN: multi_model_runner failed"

echo "Done. Check reports/backtests/promotion_candidate_1_check/multi_model/out/ for board_verdict.md"
