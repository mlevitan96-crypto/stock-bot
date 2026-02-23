# Exit review — droplet run with real data

**Run:** 2026-02-23 (via `scripts/run_exit_review_on_droplet.py`)  
**Data:** Droplet logs (attribution.jsonl + exit_attribution.jsonl), last 14 days.

---

## Results

### Exit effectiveness v2
- **Joined trades:** 2,671
- **Overall:** avg_pnl -0.1074 USD, wins 798, losses 1,685
- **By regime:** mixed 1,459, BEAR 1,069, unknown 105, NEUTRAL 38
- **Top exit reasons:** other (671), signal_decay(0.96) (245), signal_decay(0.90) (107), signal_decay(0.88) (105), …; trail_stop (5 trades, avg_pnl +2.47)
- **Giveback / saved_loss / left_money:** None/0 in current join (exit_quality_metrics not yet populated in join); effectiveness v2 structure ready for when they are.

### Dashboard truth audit
- **All 6 panels:** Live Trades PASS, Expectancy Gate WARN (stale), Signal Health WARN (stale), Score Telemetry WARN (stale), UW Cache PASS, **Exit Truth PASS**
- **Decision:** DASHBOARD_TRUTH_LOCKED

### Tuning recommendations
- Generated from effectiveness v2; many exit_reason_code buckets with saved_loss_rate 0% → consider earlier exit or threshold/weight tweaks (Board review before applying).

### Artifacts
- **On droplet:** `reports/exit_review/exit_effectiveness_v2.{json,md}`, `exit_tuning_recommendations.md`, `exit_tuning_patch.json`; `logs/exit_truth.jsonl` bootstrapped.
- **Fetched locally:** same files under `reports/exit_review/`; `dashboard_truth_droplet.json` (panel results).

---

## Next steps
1. Wire EOD to run exit effectiveness v2 + dashboard audit (see EOD_EXIT_ENFORCEMENT.md).
2. Populate exit_quality_metrics (mfe, mae, profit_giveback, saved_loss, left_money) in attribution/exit join so effectiveness v2 can report giveback/saved_loss.
3. When ready, enable EXIT_PRESSURE_ENABLED=1 on droplet for shadow or live pressure-driven exits; re-run effectiveness after a period to compare.
