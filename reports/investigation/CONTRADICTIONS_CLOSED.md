# Contradictions closed (Phase 3)

Evidence and fixes from droplet. Each contradiction: root cause, fix, re-run proof.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
# After fixes: run baseline, gate truth report, full signal review
python3 scripts/investigation_baseline_snapshot_on_droplet.py
export EXPECTANCY_GATE_TRUTH_LOG=1
# ... run until >= 200 gate truth lines ...
python3 scripts/expectancy_gate_truth_report_200_on_droplet.py
python3 scripts/full_signal_review_on_droplet.py --days 7
```

---

## 1) Ledger join coverage 0%

- **Root cause:** (To be filled from droplet evidence: timestamp mismatch / schema drift / wrong path / parsing bug.)
- **Fix:** (Telemetry/join/metric applied.)
- **Droplet proof:** (File path + counts/% after re-run.)

---

## 2) Pre-adjust median 0.000

- **Root cause:** (Missing field default / wrong field / normalization bug.)
- **Fix:** (Field source + availability rate; no default-to-zero without explicit labeling.)
- **Droplet proof:** (Score pre_adjust p50 and availability rate from funnel/gate truth.)

---

## 3) “Paper trades” non-zero while submits zero

- **Root cause:** (Metric definition bug / time window mismatch.)
- **Fix:** Renamed to candidates_evaluated, paper_orders_submitted, paper_fills; funnel and reconciliation report use these.
- **Droplet proof:** (submit_order_called.jsonl count vs paper_fills from orders.jsonl.)

---

*Update this file after each root-cause and re-run on droplet.*
