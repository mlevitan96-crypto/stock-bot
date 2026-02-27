# Follow-up diagnostics synthesis and next steps

**Run:** `followup_diag_20260222T225611Z`  
**Base run:** `alpaca_monday_final_20260222T174120Z`

---

## What was done

1. **Status script** — Saved as `scripts/quick_status_followup_run.sh`; ran on droplet and confirmed artifacts.
2. **Missing compare/index** — `scripts/finish_followup_compare_and_index.sh` was added and run for this RUN_ID so `compare_summary.md` and `ARTIFACT_INDEX.md` exist.
3. **Artifacts pulled locally** — `reports/followup_diag_artifacts/` (board_verdict.md, exec_sensitivity.json, compare_summary.md, ARTIFACT_INDEX.md).

---

## Summary of results

| Artifact | Status | Note |
|----------|--------|------|
| **Exec sensitivity** | Done | 3 runs (0, 0.05%, 0.1% slippage). PnL identical ($16,623.74) — slippage may not be applied in sim or not in metrics. |
| **Multi-model** | Done | Board verdict **ACCEPT**; prosecutor/defender/SRE + board_verdict.md in place. |
| **Exit sweep** | Stub only | `exit_sweep_summary.json` has `"status": "stub"`; no MFE/MAE or exit candidates yet. |
| **Experiments** | Done (no effect) | All three overlays show same metrics as each other ($16,623.74, 10,715 trades) — simulation does not apply overlay (composite_weights/exit params). |

**Baseline (Monday final):** net_pnl $18,811.44, 10,715 trades, 51.18% win rate.  
**Follow-up sim runs:** $16,623.74 — likely due to lab-mode or no postprocess; ~$2.2k lower.

---

## Prioritized remediation and promotion plan

### 1. Promotion (done)

- Board verdict is **ACCEPT**. Monday final run has 10,715 trades and full artifacts.
- **Recommendation:** Treat **alpaca_monday_final_20260222T174120Z** as promoted for gate_p50 and net_pnl baseline.

### 2. Exit sweep (optional)

- Current implementation is a stub. To get MFE/MAE and exit candidates:
  - Implement real exit optimization in `run_exit_optimization_on_droplet.py`, or
  - Run whatever full exit sweep script you have and point `--out` to `reports/backtests/<RUN_ID>/exit_sweep`.

### 3. Exec sensitivity (optional)

- All three slippage runs completed; PnL unchanged across 0 / 0.05% / 0.1%.
- If you want sensitivity evidence: ensure the simulation applies `slippage_model` to fills and re-run; then compare net_pnl across runs.

### 4. Overlay experiments (optional)

- Overlay configs are merged into temp configs but the simulation does not read `_overlay` / composite_weights / exit params.
- To get real tuning comparisons: add overlay support in `run_simulation_backtest_on_droplet.py` (e.g. apply `composite_weights`, `exit.*`) and re-run the three experiments.

### 5. Re-run status anytime

On droplet:
```bash
cd /root/stock-bot && bash scripts/quick_status_followup_run.sh
```
To regenerate only compare + index for an existing follow-up run:
```bash
RUN_ID=followup_diag_20260222T225611Z bash scripts/finish_followup_compare_and_index.sh
```

---

## Key artifact paths (droplet)

- Exec sensitivity: `reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/exec_sensitivity.json`
- Multi-model: `reports/backtests/followup_diag_20260222T225611Z/multi_model/` (board_verdict.md, board_verdict.json)
- Exit sweep: `reports/backtests/followup_diag_20260222T225611Z/exit_sweep/exit_sweep_summary.json` (stub)
- Experiments compare: `reports/backtests/followup_diag_20260222T225611Z/experiments/compare_summary.md`
- Index: `reports/backtests/followup_diag_20260222T225611Z/ARTIFACT_INDEX.md`
- Base attribution: `reports/backtests/alpaca_monday_final_20260222T174120Z/attribution/per_signal_pnl.json`
- Base ablation: `reports/backtests/alpaca_monday_final_20260222T174120Z/ablation/ablation_summary.json`
- Base metrics: `reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/metrics.json`
